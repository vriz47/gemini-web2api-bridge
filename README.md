# gemini-web2api bridge (Termux)

Gemini Web -> OpenAI-compatible API proxy, dioptimasi untuk dipakai di Termux/Android bareng
[kapan? opencode](https://opencode.ai) atau client OpenAI lain.

Berdasarkan [X-shuffle/gemini-web2api](https://github.com/X-shuffle/gemini-web2api) (MIT),
dengan penyesuaian:

- **Cookie auth**: satu baris cookie `gemini.google.com` di `config/cookies.txt` (lihat
  `config/cookies.example`). Kosong = mode anonymous untuk model free.
- **XSRF self-heal**: kalau StreamGenerate balas HTTP 400, token `xsrf` otomatis diekstrak
  dari body error, disimpan ke `config/xsrf.txt`, lalu request langsung di-retry (200).
- **Vision**: part OpenAI `image_url` (data URL base64 atau URL http) di-upload via Scotty
  (`content-push.googleapis.com`) jadi file ref, lalu di-bind ke StreamGenerate. Streaming
  dan non-streaming jalan.

## Menjalankan

```bash
pip install httpx
./manage.sh start      # jalankan di background 127.0.0.1:8787
./manage.sh status     # cek status
./manage.sh restart    # restart
```

## Konfigurasi

Salin `config/config.example.json` menjadi `config/config.json` lalu sesuaikan
`cookie_file` / `xsrf_file`. Cookie dan token XSRF TIDAK boleh di-commit
(lihat `.gitignore`).

## Client

```
Base URL: http://127.0.0.1:8787/v1
Model   : gemini-3.5-flash, gemini-3.5-flash-thinking, gemini-3.1-pro, ...
```

## Capture cookie otomatis

Cookie login `gemini.google.com` (termasuk yang HttpOnly) diambil dari **Kiwi Browser NEXT**
(membutuhkan extension, karena CDP/remote-debugging sudah hilang di Chromium modern).

1. Jalankan listener di Termux:
   ```bash
   python3 capture_cookies.py --serve   # listener 127.0.0.1:8899
   ```
2. Buka `kiwi://extensions` di Kiwi NEXT → aktifkan Developer mode → Load unpacked
   → pilih folder `kiwi-cookie-ext/` (atau zip jadi `kiwi-cookie-ext.zip` lalu Load zip).
3. Login ke `gemini.google.com` di Kiwi. Extension membaca `chrome.cookies` (baca
   HttpOnly) dan mengirim ke listener setiap ~2 detik; cookie ditulis ke
   `config/cookies.txt` dalam satu baris.

Catatan:
- MV2 sudah mati — butuh Kiwi NEXT (MV3), bukan Kiwi classic/playstore.
- Session login Google sekarang = skema konsolidasi 9 cookie
  (`__Secure-1PSID`, `SAPISID`, `NID`, dsb.; `SID`/`HSID`/`APISID` memang tidak ada lagi).
- `capture_cookies.py --serve` hanya mendengarkan di `127.0.0.1`.

## Credits

Proyek ini berdasar / memakai pola dari:

- [X-shuffle/gemini-web2api](https://github.com/X-shuffle/gemini-web2api) (MIT) — basis
  `gemini_web2api.py` (proxy chat + StreamGenerate).
- [ZmoleCristian/gemini-web-image](https://github.com/ZmoleCristian/gemini-web-image) —
  struktur payload StreamGenerate dengan binding file (inner array + model id image).
- [HanaokaYuzu/Gemini-API](https://github.com/HanaokaYuzu/Gemini-API) — protokol upload
  Scotty ke `content-push.googleapis.com` + ekstraksi page token (`qKIAYe`, `pctx`).

Perincian hak cipta ada di `LICENSE` (MIT). Terima kasih kepada para penulis di atas.