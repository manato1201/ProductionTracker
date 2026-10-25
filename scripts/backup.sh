#!/usr/bin/env bash
# pg_dump(カスタム形式)を backups/ に保存する。毎日 cron などで実行する想定。
#   ./scripts/backup.sh
# 環境変数:
#   BACKUP_DIR          保存先(既定 ./backups。Git には入れない)
#   BACKUP_KEEP         残す世代数(既定 14)
#   BACKUP_RCLONE_DEST  設定すると rclone copy で外部(例: Cloudflare R2 の `r2:bucket/path`)にも保存する(rclone と設定が別途必要)
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/lib.sh

dir="${BACKUP_DIR:-./backups}"
keep="${BACKUP_KEEP:-14}"
mkdir -p "$dir"
stamp="$(date +%Y%m%d-%H%M%S)"
file="$dir/pt-$stamp.dump"

umask 077  # バックアップには全データが入る。自分だけが読めるようにする
run_pg pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$file.tmp"
mv "$file.tmp" "$file"
row_counts "$POSTGRES_DB" > "$file.counts"
echo "保存しました: $file ($(du -h "$file" | cut -f1))"
cat "$file.counts"

# 古い世代を消す
ls -1t "$dir"/pt-*.dump 2>/dev/null | tail -n +"$((keep + 1))" | while read -r old; do
  rm -f "$old" "$old.counts"
  echo "古いバックアップを削除: $old"
done

if [ -n "${BACKUP_RCLONE_DEST:-}" ]; then
  rclone copy "$file" "$BACKUP_RCLONE_DEST" && rclone copy "$file.counts" "$BACKUP_RCLONE_DEST"
  echo "rclone で保存しました: $BACKUP_RCLONE_DEST"
fi
