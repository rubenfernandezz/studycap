(async () => {
  if (location.origin !== "http://127.0.0.1:5050" || location.pathname !== "/import") return;
  const id = location.hash.slice(1);
  if (!/^[\da-f-]{36}$/.test(id)) return;
  const status = document.querySelector("#handoff");
  if (!status) return;
  history.replaceState(null, "", "/import");
  try {
    const result = await chrome.runtime.sendMessage({ type: "read", id });
    if (!result?.ok) throw new Error();
    document.querySelector("#title").value = result.title;
    document.querySelector("#captions").value = result.captions;
    status.textContent = "Captions received from the extension. Review them before saving.";
  } catch {
    status.textContent = "The capture expired or was already opened. Capture the lecture again.";
  }
})();
