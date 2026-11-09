const { test } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { randomUUID } = require("node:crypto");

function workerFixture() {
  const stored = {};
  const opened = [];
  const extension = "chrome-extension://example";
  let listener;
  const chrome = {
    runtime: { getURL: name => extension + "/" + name, onMessage: { addListener: fn => { listener = fn; } } },
    tabs: { create: async tab => { opened.push(tab.url); } },
    storage: { session: {
      get: async () => ({ ...stored }),
      set: async items => Object.assign(stored, items),
      remove: async keys => { for (const key of [].concat(keys)) delete stored[key]; }
    } }
  };
  vm.runInNewContext(readFileSync(path.join(__dirname, "../background.js"), "utf8"),
                     { chrome, URL, crypto: { randomUUID } });
  const send = (message, sender) => new Promise(resolve => listener(message, sender, resolve));
  return { stored, opened, send, popup: { url: extension + "/popup.html" } };
}

test("the review page receives a staged capture once", async () => {
  const { send, popup, opened, stored } = workerFixture();
  assert.equal((await send({ type: "stage", title: "Practice", captions: "Synthetic captions" }, popup)).ok, true);
  const url = new URL(opened[0]);
  assert.equal(url.origin, "http://127.0.0.1:5050");
  const id = url.hash.slice(1);
  const reader = { tab: {}, frameId: 0, url: url.href };
  assert.equal((await send({ type: "read", id }, { ...reader, url: "http://127.0.0.1:5001/import" })).ok, false);
  const [first, second] = await Promise.all([send({ type: "read", id }, reader), send({ type: "read", id }, reader)]);
  assert.equal(first.captions, "Synthetic captions");
  assert.equal(second.ok, false);
  assert.equal(Object.keys(stored).length, 0);
});

test("unread expired captures are pruned on the next message", async () => {
  const { send, popup, opened, stored } = workerFixture();
  await send({ type: "stage", title: "Practice", captions: "Synthetic captions" }, popup);
  const id = new URL(opened[0]).hash.slice(1);
  stored["capture-" + id].expires = 0;
  const result = await send({ type: "read", id }, { tab: {}, frameId: 0, url: opened[0] });
  assert.equal(result.ok, false);
  assert.equal(Object.keys(stored).length, 0);
});
