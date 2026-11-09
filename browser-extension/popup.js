const appOrigin = "http://127.0.0.1:5050";
const capture = document.querySelector("#capture");
const statusLine = document.querySelector("#status");
async function requireLocalApp() {
  try {
    const response = await fetch(appOrigin + "/status", {
      credentials: "omit", cache: "no-store", redirect: "error", signal: AbortSignal.timeout(3500)
    });
    if (response.ok && await response.text() === "studycap-local-v1") return;
  } catch {
    // A stopped server, timeout or blocked connection has the same recovery step.
  }
  throw new Error("Start the StudyCap web app at 127.0.0.1:5050, then try again.");
}

document.querySelector("#practice").addEventListener("click", async () => {
  try {
    await requireLocalApp();
    await chrome.tabs.create({ url: appOrigin + "/practice" });
  } catch (error) {
    statusLine.textContent = error.message;
  }
});

capture.addEventListener("click", async () => {
  capture.disabled = true;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = new URL(tab.url);
    const practice = url.origin === appOrigin && url.pathname === "/practice";
    const panopto = url.protocol === "https:" && /(?:^|\.)panopto\.(?:eu|com)$/.test(url.hostname);
    if (!practice && !panopto) throw new Error("Open a Panopto lecture or the local practice page.");
    await requireLocalApp();
    const [frame] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
    const {title, captions} = frame.result;
    if (!captions.trim()) throw new Error("Open the captions panel first, then capture again.");
    if (captions.length > 60000) throw new Error("This transcript exceeds the local 60,000-character limit.");
    const response = await chrome.runtime.sendMessage({ type: "stage", title: title.slice(0, 200), captions });
    if (!response?.ok) throw new Error("The review tab could not be opened.");
    window.close();
  } catch (error) {
    statusLine.textContent = error.message || "Capture failed. Reopen the popup and try again.";
    capture.disabled = false;
  }
});
