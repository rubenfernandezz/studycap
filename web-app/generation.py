"""Offline study exercises and an opt-in loopback chat-completions adapter."""
import http.client
import json
import os
import re

from study_tools import build_messages


def configured_model():
    name = os.getenv("STUDYCAP_MODEL", "").strip()
    port = os.getenv("STUDYCAP_MODEL_PORT", "").strip()
    if not name and not port:
        return None
    if not name or not port.isdecimal() or not 1 <= int(port) <= 65535:
        raise ValueError("Set both a local model name and a valid port in .env.")
    return name, int(port)


def generate(kind, data, model):
    if model is None:
        return offline(kind, data)
    name, port = model
    payload = {"model": name, "messages": build_messages(kind, data)}
    if kind == "quiz":
        payload["response_format"] = {"type": "json_object"}
    client = http.client.HTTPConnection("127.0.0.1", port, timeout=60)
    try:
        client.request("POST", "/v1/chat/completions", json.dumps(payload),
                       {"Content-Type": "application/json"})
        response = client.getresponse()
        if response.status != 200:
            raise ValueError("The local model declined the request.")
        raw = response.read(512_001)
        if len(raw) > 512_000:
            raise ValueError("The local model response exceeded the size limit.")
        result = json.loads(raw)["choices"][0]["message"]["content"]
        if not isinstance(result, str) or not result.strip() or len(result) > 100_000:
            raise ValueError("The local model returned an empty or oversized result.")
        return result
    except (OSError, http.client.HTTPException, ValueError, IndexError, KeyError, TypeError) as exc:
        raise ValueError("Check the loopback model server and its response format.") from exc
    finally:
        client.close()


def offline(kind, data):
    if kind == "summary":
        sections = []
        for field, heading in (("captions", "Caption excerpts"), ("pdfText", "Slide excerpts")):
            lines = [line.strip() for line in data.get(field, "").splitlines() if line.strip()]
            if lines:
                excerpts = list(dict.fromkeys(lines))[:8]
                sections.append(heading + "\n" + "\n".join(excerpts))
        return "\n\n".join(sections)
    lines = [line for line in data["summaryText"].splitlines() if line.strip()
             and line not in ("Caption excerpts", "Slide excerpts")]
    if kind == "chat":
        terms = set(re.findall(r"\w{3,}", data["userQuestion"].lower()))
        ranked = sorted(lines, key=lambda line: len(terms & set(re.findall(r"\w+", line.lower()))),
                        reverse=True)
        matches = [line for line in ranked if terms & set(re.findall(r"\w+", line.lower()))]
        return "\n".join(matches[:3]) or "No matching passage found in these notes."
    exercises = []
    for line in lines[:3]:
        word = max(re.findall(r"[A-Za-z]{4,}", line), key=len, default="")
        if word:
            exercises.append((line.replace(word, "____", 1), word))
    return exercises
