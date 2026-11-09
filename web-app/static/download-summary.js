// The shared lecture formatter operates only on HTML-escaped plain text.
(() => {
  function parseSummaryToHTML(rawSummary) {
    const lines = escapeHTML(rawSummary).split("\n");
    let htmlOutput = "";
    let mathBlockLines = null;
    let currentIndentLevel = 0;
    let inBulletList = false;
    let listType = null;
  
    for (let line of lines) {
        if (mathBlockLines !== null) {
            mathBlockLines.push(line);
            if (line.trim().endsWith("\\]")) {
                htmlOutput += mathBlockLines.join("\n");
                mathBlockLines = null;
            }
            continue;
        }
  
        if (line.trim().startsWith("\\[") && !line.trim().endsWith("\\]")) {
            mathBlockLines = [line];
            continue;
        }
  
        if (line.trim().startsWith("\\[") && line.trim().endsWith("\\]")) {
            htmlOutput += line;
            continue;
        }
  
        const indentMatch = line.match(/^(\s*)/);
        const indent = indentMatch ? indentMatch[0].length : 0;
        const trimmedLine = line.trim();
        const isBulletPoint = trimmedLine.startsWith("* ");
        const isDashPoint = trimmedLine.startsWith("- ");
        const isListItem = isBulletPoint || isDashPoint;
        const newListType = isBulletPoint ? 'bullet' : isDashPoint ? 'dash' : null;
        
        if (inBulletList && (indent !== currentIndentLevel || newListType !== listType)) {
            htmlOutput += "</ul>";
            inBulletList = false;
            listType = null;
        }
  
        if (line.startsWith("## ")) {
            htmlOutput += `<h2>${line.replace("## ", "")}</h2>`;
        } else if (line.startsWith("### ")) {
            htmlOutput += `<h3>${line.replace("### ", "")}</h3>`;
        } else if (line.startsWith("#### ")) {
            htmlOutput += `<h4>${line.replace("#### ", "")}</h4>`;
        } else if (line.startsWith("# ")) {
            htmlOutput += `<h1>${line.replace("# ", "")}</h1>`;
        } else if (isListItem) {
            if (!inBulletList) {
                htmlOutput += `<ul>`;
                inBulletList = true;
                currentIndentLevel = indent;
                listType = newListType;
            }
            const content = parseBold(trimmedLine.replace(/^[*\-]\s+/, ""));
            htmlOutput += `<li>${content}</li>`;
        } else {
            const parsedLine = parseBold(line);
            if (parsedLine.trim()) {
                htmlOutput += `<p>${parsedLine}</p>`;
            }
        }
    }
  
    if (inBulletList) {
        htmlOutput += "</ul>";
    }
  
    return htmlOutput;
  }

  function parseBold(text) {
    return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  }

  function escapeHTML(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
  const notes = document.querySelector("#study-notes");
  if (!notes) return;
  notes.innerHTML = parseSummaryToHTML(notes.textContent);
  document.querySelector("#export-doc").addEventListener("click", () => {
    const title = document.querySelector("h1").textContent;
    const annotations = document.querySelector("#personal-notes")?.textContent || "";
    const docContent = '<!doctype html><html><head><meta charset="utf-8"><title>' + escapeHTML(title) +
      '</title></head><body><h1>' + escapeHTML(title) + '</h1>' + notes.innerHTML +
      (annotations ? '<h2>Personal notes</h2><pre>' + escapeHTML(annotations) + '</pre>' : '') + '</body></html>';
    const blob = new Blob([docContent], { type: "application/msword" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "studycap-notes.doc";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
})();
