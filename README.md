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

`capture_cookies.py --serve` membuka listener 127.0.0.1:8899 untuk menerima cookie dari
extension browser (baca `chrome.cookies`, termasuk HttpOnly) dan menulis `config/cookies.txt`.