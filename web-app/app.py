from pathlib import Path
import secrets
import json

from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template, request, session, url_for

from db import close_database, database, initialize
from documents import extract_text
from generation import configured_model, generate
from study_tools import score_and_filter_videos

CAPTIONS = (
    "A feedback controller compares the measured output with a desired setpoint.",
    "The error signal is the difference between the setpoint and the measured output.",
    "Proportional control multiplies the error by a gain to calculate the control action.",
    "Integral control accumulates the error over time and can reduce steady-state error.",
)
RESOURCES = (
    {"title": "Feedback control basics", "duration": "8:30", "description": "Synthetic overview"},
    {"title": "Integral control worked example", "duration": "16:00", "description": "Synthetic example"},
    {"title": "Advanced signal processing", "duration": "45:00", "description": "Synthetic lecture"},
)


def quiz_questions(raw):
    try:
        payload = json.loads(raw)
        questions = payload.get("questions") if isinstance(payload, dict) else payload
        if not isinstance(questions, list) or not 1 <= len(questions) <= 10:
            raise ValueError
        for question in questions:
            if (not isinstance(question, dict) or not isinstance(question.get("question"), str)
                    or question.get("correctAnswer") not in ("A", "B", "C", "D")
                    or not isinstance(question.get("options"), list) or len(question["options"]) != 4
                    or not all(isinstance(option, str) for option in question["options"])
                    or not isinstance(question.get("explanation"), str)):
                raise ValueError
        return questions
    except (ValueError, TypeError) as exc:
        raise ValueError("The local model returned a quiz in an unsupported format.") from exc


def create_app(data_dir=None):
    app = Flask(__name__)
    load_dotenv(Path(__file__).with_name(".env"))
    directory = Path(data_dir or app.instance_path)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "portfolio.sqlite3"
    model = configured_model()
    app.config.update(SECRET_KEY=initialize(path), MAX_CONTENT_LENGTH=8 * 1024 * 1024,
                      TRUSTED_HOSTS=["127.0.0.1"], SESSION_COOKIE_SAMESITE="Strict",
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_NAME="studycap_portfolio")
    app.teardown_appcontext(close_database)

    @app.before_request
    def check_session():
        if request.endpoint == "status":
            return
        if "owner" not in session:
            session["owner"] = secrets.token_hex(24)
            session["csrf"] = secrets.token_hex(24)
        if request.method == "POST":
            token = request.form.get("csrf", "")
            if not token.isascii() or not secrets.compare_digest(token, session["csrf"]):
                abort(403)

    @app.after_request
    def headers(response):
        response.headers.update({
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'",
            "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        })
        return response

    def lookup(lecture_id):
        row = database(path).execute("SELECT * FROM lectures WHERE id=? AND owner=?",
                                     (lecture_id, session["owner"])).fetchone()
        if row is None:
            abort(404)
        return row

    def display(lecture, **context):
        resources = score_and_filter_videos([dict(item) for item in RESOURCES],
                                            lecture["summary"], lecture["title"])
        return render_template("lecture_viewer.html", lecture=lecture, model=model,
                               resources=resources, **context)

    @app.get("/status")
    def status():
        # Only this public status marker is readable across origins. No user data or cookie.
        return "studycap-local-v1", 200, {"Access-Control-Allow-Origin": "*"}

    @app.get("/")
    def dashboard():
        rows = database(path).execute(
            "SELECT id, title, updated FROM lectures WHERE owner=? ORDER BY updated DESC, rowid DESC",
            (session["owner"],))
        return render_template("dashboard.html", lectures=rows)

    @app.get("/practice")
    def practice():
        return render_template("practice.html", captions=CAPTIONS)

    @app.route("/import", methods=["GET", "POST"])
    def capture():
        if request.method == "GET":
            sample = request.args.get("sample") == "1"
            return render_template("capture.html", title="Feedback control" if sample else "",
                                   captions="\n".join(CAPTIONS) if sample else "", model=model)
        title = request.form.get("title", "").strip()
        captions = request.form.get("captions", "").strip()
        try:
            if not title or len(title) > 200 or len(captions) > 60_000:
                raise ValueError("Enter a title up to 200 characters and at most 60,000 caption characters.")
            slides = extract_text(request.files.get("slides"))
            if not captions and not slides:
                raise ValueError("Add captions or a document with selectable text.")
            summary = generate("summary", {"captions": captions, "pdfText": slides}, model)
            if len(summary) > 100_000:
                raise ValueError("The combined notes exceed 100,000 characters.")
        except ValueError as exc:
            return render_template("capture.html", title=title, captions=captions,
                                   error=str(exc), model=model), 400
        lecture_id = secrets.token_hex(12)
        with database(path) as db:
            db.execute("INSERT INTO lectures(id,owner,title,summary) VALUES(?,?,?,?)",
                       (lecture_id, session["owner"], title, summary))
        return redirect(url_for("viewer", lecture_id=lecture_id), code=303)

    @app.get("/lectures/<lecture_id>")
    def viewer(lecture_id):
        return display(lookup(lecture_id))

    @app.post("/lectures/<lecture_id>/edit")
    def edit(lecture_id):
        lecture = lookup(lecture_id)
        title, summary, notes = (request.form.get(key, "").strip() for key in ("title", "summary", "notes"))
        if not title or not summary or len(title) > 200 or max(len(notes), len(summary)) > 100_000:
            return display(lecture, error="The title and study notes must fit the displayed limits."), 400
        with database(path) as db:
            db.execute("UPDATE lectures SET title=?,summary=?,notes=?,updated=CURRENT_TIMESTAMP WHERE id=? AND owner=?",
                       (title, summary, notes, lecture_id, session["owner"]))
        return redirect(url_for("viewer", lecture_id=lecture_id), code=303)

    @app.post("/lectures/<lecture_id>/remove")
    def remove(lecture_id):
        lookup(lecture_id)
        with database(path) as db:
            db.execute("DELETE FROM lectures WHERE id=? AND owner=?", (lecture_id, session["owner"]))
        return redirect(url_for("dashboard"), code=303)

    @app.post("/lectures/<lecture_id>/study")
    def study(lecture_id):
        lecture = lookup(lecture_id)
        kind = request.form.get("action")
        question = request.form.get("question", "").strip()
        if kind not in {"chat", "quiz"} or len(question) > 2_000 or (kind == "chat" and not question):
            abort(400)
        try:
            result = generate(kind, {"summaryText": lecture["summary"], "userQuestion": question}, model)
            if kind == "quiz" and model:
                result = quiz_questions(result)
        except ValueError as exc:
            return display(lecture, error=str(exc)), 400
        return display(lecture, result=result, action=kind, question=question)

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5050, debug=False)
