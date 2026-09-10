#!/data/data/com.termux/files/usr/bin/bash
# Kelola bridge Gemini Web <-> OpenAI API.
#
# Usage:
#   ./manage.sh start       jalankan bridge di background (127.0.0.1:8787)
#   ./manage.sh stop        stop bridge
#   ./manage.sh restart     restart bridge
#   ./manage.sh status      cek status / proses
#   ./manage.sh logs        ikuti log bridge
#   ./manage.sh cookie      pasang cookie (edit config/cookies.txt)
set -e
cd "$(dirname "$0")"
LOG=/data/data/com.termux/files/usr/tmp/opencode/bridge.log
PID=$(pgrep -f "gemini_web2api.py --config config/config.json" | head -1 || true)

case "$1" in
  start)
    if [ -n "$PID" ]; then echo "Sudah jalan (pid $PID)"; exit 0; fi
    setsid python3 gemini_web2api.py --config config/config.json >"$LOG" 2>&1 < /dev/null &
    disown
    sleep 2
    echo "Start. Log: $LOG"
    ;;
  stop)
    if [ -n "$PID" ]; then kill "$PID"; echo "Stopped ($PID)"; else echo "Tidak ada proses"; fi
    ;;
  restart)
    "$0" stop || true
    sleep 1
    "$0" start
    ;;
  status)
    if [ -n "$PID" ]; then echo "RUNNING pid=$PID — $(curl -s --max-time 3 http://127.0.0.1:8787/ || true)"; else echo "STOPPED"; fi
    ;;
  logs)
    tail -f "$LOG"
    ;;
  cookie)
    "$PWD/../bin/edit-cookie" 2>/dev/null || nano config/cookies.txt
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs|cookie}"
    ;;
esac