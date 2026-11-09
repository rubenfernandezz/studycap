const appOrigin = "http://127.0.0.1:5050";
const prefix = "capture-";
const lifetime = 120000;

async function handle(message, sender) {
  const now = Date.now();
  const items = await chrome.storage.session.get(null);
  const expired = Object.keys(items).filter(key => key.startsWith(prefix) && items[key].expires <= now);
  if (expired.length) await chrome.storage.session.remove(expired);

  if (message.type === "stage" && sender.url === chrome.runtime.getURL("popup.html")) {
    if (typeof message.title !== "string" || typeof message.captions !== "string" ||
        !message.captions.trim() || message.captions.length > 60000) return { ok: false };
    const id = crypto.randomUUID();
    const key = prefix + id;
    await chrome.storage.session.set({ [key]: { title: message.title.slice(0, 200),
      captions: message.captions, expires: now + lifetime } });
    try {
      await chrome.tabs.create({ url: appOrigin + "/import#" + id });
      return { ok: true };
    } catch (error) {
      await chrome.storage.session.remove(key);
      throw error;
    }
  }

  if (message.type === "read" && sender.tab && sender.frameId === 0) {
    const url = new URL(sender.url);
    if (url.origin !== appOrigin || url.pathname !== "/import" || !/^[\da-f-]{36}$/.test(message.id)) {
      return { ok: false };
    }
    const key = prefix + message.id;
    const item = items[key];
    if (!item || item.expires <= now) return { ok: false };
    await chrome.storage.session.remove(key);
    return { ok: true, title: item.title, captions: item.captions };
  }
  return { ok: false };
}

// Session storage has no atomic read-and-remove operation. Serialize handoffs so
// two review tabs cannot both consume the same capture.
let pending = Promise.resolve();
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  pending = pending.then(() => handle(message, sender)).then(respond, () => respond({ ok: false }));
  return true;
});
