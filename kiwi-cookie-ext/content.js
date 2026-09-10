function getXsrf() {
  try {
    const ss = document.querySelectorAll("script");
    for (const s of ss) {
      const m = s.textContent.match(/"SNlM0e","([^"]+)"/);
      if (m) return m[1];
    }
  } catch (e) {}
  return null;
}
function wake() {
  try { chrome.runtime.sendMessage({ t: "wake", xsrf: getXsrf() }); } catch (e) {}
}
wake();
setInterval(wake, 2000);