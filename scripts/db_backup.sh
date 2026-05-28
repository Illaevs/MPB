#!/usr/bin/env bash
# Tiered DB backup for the CRM test-portal SQLite database.
#
# Usage: db_backup.sh {hot|warm|daily|weekly}
#
# - hot    : every 5 min, keep 12 (≈ last hour, uncompressed for speed)
# - warm   : every hour,  keep 24 (≈ last 24 hours, uncompressed)
# - daily  : every day,   keep 30 (≈ last month, gzipped)
# - weekly : every Sunday,keep 52 (≈ last year, gzipped)
#
# Consistent snapshot is taken via Python sqlite3.backup() API — safe
# with the running service under WAL. Each tier rotates independently.
set -eu

TIER="${1:-}"
if [ -z "$TIER" ]; then
  echo "usage: $0 hot|warm|daily|weekly" >&2
  exit 2
fi

DB="/opt/mpb-erp-test/test_portal/crm_test_portal.db"
PYV="/opt/mpb-erp-test/venv/bin/python"
ROOT="/mnt/storage20/db_backups"
DIR="$ROOT/$TIER"
TS="$(date +%Y%m%d-%H%M%S)"

case "$TIER" in
  hot)    KEEP=12;  GZIP=0 ;;
  warm)   KEEP=24;  GZIP=0 ;;
  daily)  KEEP=30;  GZIP=1 ;;
  weekly) KEEP=52;  GZIP=1 ;;
  *) echo "unknown tier: $TIER" >&2; exit 2 ;;
esac

mkdir -p "$DIR"
chmod 0700 "$ROOT" "$DIR" 2>/dev/null || true

OUT="$DIR/crm_test_portal.$TS.db"

# Consistent snapshot. .backup() iterates pages with brief locks,
# does not block writers for any meaningful time.
"$PYV" - "$DB" "$OUT" <<'PY'
import sqlite3, sys
src = sqlite3.connect(sys.argv[1])
dst = sqlite3.connect(sys.argv[2])
with dst:
    src.backup(dst)
src.close(); dst.close()
PY

if [ "$GZIP" = "1" ]; then
  gzip -f "$OUT"
  OUT="${OUT}.gz"
fi

# Retention: keep only the newest $KEEP files (including the one we just
# wrote). `ls -1t` sorts newest-first; tail +N drops the head, rm cleans
# the tail.
PATTERN="$DIR"/crm_test_portal.*
# Use shell glob via find to avoid `ls | xargs` quoting issues.
mapfile -t ALL < <(find "$DIR" -maxdepth 1 -name 'crm_test_portal.*' -printf '%T@ %p\n' | sort -rn | awk '{print $2}')
if [ "${#ALL[@]}" -gt "$KEEP" ]; then
  for f in "${ALL[@]:$KEEP}"; do
    rm -f "$f"
  done
fi

SIZE=$(stat -c%s "$OUT")
echo "$(date -Iseconds) [$TIER] -> $OUT ($SIZE bytes, retain=$KEEP)"
