#!/usr/bin/env bash
# バックアップを「別の DB」に復元し、バックアップ時の件数と一致するか確認する。
#   ./scripts/restore.sh backups/pt-20261025-090000.dump [復元先DB名]
# 復元先の既定は `<POSTGRES_DB>_restore`。稼働中の DB を上書きしたいときだけ
#   RESTORE_OVERWRITE=1 ./scripts/restore.sh <dump> "$POSTGRES_DB"   (先に web を止めること)
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/lib.sh

dump="${1:?使い方: restore.sh <dumpファイル> [復元先DB名]}"
target="${2:-${POSTGRES_DB}_restore}"
[ -f "$dump" ] || { echo "ファイルがありません: $dump" >&2; exit 2; }

if [ "$target" = "$POSTGRES_DB" ] && [ "${RESTORE_OVERWRITE:-0}" != "1" ]; then
  echo "稼働中の DB($POSTGRES_DB)への上書きは RESTORE_OVERWRITE=1 を付けたときだけ行います。" >&2
  exit 2
fi

run_pg dropdb -U "$POSTGRES_USER" --if-exists "$target"
run_pg createdb -U "$POSTGRES_USER" "$target"
run_pg pg_restore -U "$POSTGRES_USER" -d "$target" --no-owner --exit-on-error < "$dump"
echo "復元しました: $target"

restored="$(row_counts "$target")"
echo "$restored"
if [ -f "$dump.counts" ]; then
  if [ "$restored" = "$(cat "$dump.counts")" ]; then
    echo "件数一致: OK(バックアップ時と同じ)"
  else
    echo "件数が一致しません。バックアップ時:" >&2
    cat "$dump.counts" >&2
    exit 1
  fi
else
  echo "(件数ファイル $dump.counts が無いため、突き合わせは省略)"
fi
