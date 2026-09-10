#!/usr/bin/env python3
"""Ambil cookie gemini.google.com dari:
  1. CDP remote debugging browser Chromium-based (Kiwi) -- Network.getAllCookies via WS 9222.
  2. Fallback: cookies.sqlite Firefox Android (plaintext).
Tulis hasilnya ke config/cookies.txt.

Syarat: browser sudah login ke https://gemini.google.com.
"""
import asyncio
import json
import os
import sqlite3
import subprocess
import sys
import urllib.request

HOME = os.path.expanduser("~")
OUT = os.path.join(HOME, "gemini-bridge", "config", "cookies.txt")

NEEDED_NAMES = {
    "SID", "HSID", "SSID", "APISID", "SAPISID",
    "NID", "SIDCC", "LSID", "SAPISIDHASH",
    "__Secure-1PSID", "__Secure-1PAPISID", "__Secure-1PSIDCC",
    "__Secure-3PSID", "__Secure-3PAPISID", "__Secure-3PSIDCC",
    "__Secure-1PSIDTS",
}

DOMAIN_RANK = {
    "gemini.google.com": 0,
    ".gemini.google.com": 1,
    ".google.com": 2,
    "accounts.google.com": 3,
}


def pick(names_values):
    by_name = {}
    for name, value in names_values:
        if name in NEEDED_NAMES and value:
            by_name.setdefault(name, value)
    return by_name


def write_out(got):
    if not got:
        return False
    line = "; ".join(f"{k}={got[k]}" for k in sorted(got))
    with open(OUT, "w") as f:
        f.write(line + "\n")
    os.chmod(OUT, 0o600)
    print(f"Tersimpan {len(got)} cookie -> {OUT}")
    print("Kandungan:", ", ".join(sorted(got)))
    return True


# ─── Jalur 1: CDP (Kiwi) ─────────────────────────────────────────────────────
def cdp_target():
    try:
        targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=4).read())
    except Exception:
        return None
    for t in targets:
        if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
            return t["webSocketDebuggerUrl"]
    return None


async def cdp_cookies():
    ws_url = cdp_target()
    if not ws_url:
        print("CDP: port 9222 tidak aktif / tidak ada target page.")
        return None
    try:
        import websockets
    except ImportError:
        print("CDP butuh 'websockets' (python). Install: pip install websockets")
        return None
    async with websockets.connect(ws_url, max_size=10 * 1024 * 1024, open_timeout=10) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
        await ws.recv()
        await ws.send(json.dumps({"id": 2, "method": "Network.getAllCookies"}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 2:
                cookies = (msg.get("result") or {}).get("cookies", [])
                break
    cands = []
    for c in cookies:
        domain = (c.get("domain") or "").rstrip(".")
        ds = c.get("domain") or ""
        if domain not in DOMAIN_RANK:
            continue
        cands.append((DOMAIN_RANK.get(c.get("domain"), 9), c.get("name"), c.get("value", "")))
    cands.sort(key=lambda x: x[0])
    got = pick([(n, v) for _, n, v in cands])
    return got


# ─── Jalur 2: Firefox DB ─────────────────────────────────────────────────────
FF_PKGS = [
    "org.mozilla.firefox", "org.mozilla.firefox.beta",
    "org.mozilla.fenix", "us.spotco.fennec_dos",
]


def firefox_cookies():
    found = []
    for pkg in FF_PKGS:
        r = subprocess.run(["su", "-c", f"ls -d /data/data/{pkg}/files/mozilla/*/ 2>/dev/null"],
                           capture_output=True, text=True)
        for d in r.stdout.split():
            db = os.path.join(d, "cookies.sqlite")
            chk = subprocess.run(["su", "-c", f"test -f {db} && echo ok"], capture_output=True, text=True)
            if chk.stdout.strip():
                found.append(db)
    if not found:
        print("Firefox: tidak ada cookies.sqlite.")
        return None
    db = found[0]
    print(f"Firefox DB: {db}")
    subprocess.run(["su", "-c", f"cp '{db}' /data/local/tmp/ff_cookies.db && chmod 644 /data/local/tmp/ff_cookies.db"], check=True)
    conn = sqlite3.connect("/data/local/tmp/ff_cookies.db")
    rows = conn.execute(
        "SELECT host, name, value FROM moz_cookies "
        "WHERE host IN ('.google.com','gemini.google.com','.gemini.google.com','accounts.google.com')"
    ).fetchall()
    conn.close()
    cands = [(DOMAIN_RANK.get(h, 9), n, v or "") for h, n, v in rows if n in NEEDED_NAMES]
    cands.sort(key=lambda x: x[0])
    return pick([(n, v) for _, n, v in cands])


# ─── Mode serve: listener untuk extension Kiwi ───────────────────────────────
def serve_capture():
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length) or b"{}")
                cookies = data.get("cookies")
                if not cookies:
                    print("Ping diterima tapi belum ada cookie (login dulu?)")
                    self.send_response(200); self.end_headers(); return
                got = pick([(c["name"], c["value"]) for c in cookies])
                ok = write_out(got)
                print("COOKIE DITANGKAP ->", OUT if ok else "(kosong)")
                if data.get("xsrf"):
                    with open(os.path.join(HOME, "gemini-bridge", "config", "xsrf.txt"), "w") as fh:
                        fh.write(data["xsrf"].strip())
                    print("XSRF TOKEN tersimpan")
            except Exception as e:
                print("serve_capture error:", e)
            self.send_response(200)
            self.end_headers()

    print("Listener cookie aktif di http://127.0.0.1:8899/capture")
    print("Tunggu extension Kiwi kirim cookie... (Ctrl+C untuk stop)")
    HTTPServer(("127.0.0.1", 8899), H).serve_forever()


async def main():
    if "--serve" in sys.argv:
        await serve_capture()
        return
    print("Jalur 1: CDP Kiwi (http://127.0.0.1:9222)...")
    got = await cdp_cookies()
    if got and write_out(got):
        return

    print("\nJalur 2: Firefox cookies.sqlite...")
    got = firefox_cookies()
    if got and write_out(got):
        return

    print("\nGAGAL. Pastikan:")
    print(" - Kiwi terbuka & sudah login gemini.google.com (atau Firefox),")
    print(" - Untuk Kiwi: file /data/local/tmp/chrome-command-line berisi 'chrome --remote-debugging-port=9222'.")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())