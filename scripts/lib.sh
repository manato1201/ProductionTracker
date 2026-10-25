# backup.sh / restore.sh の共通部品。
#   既定: docker compose の db コンテナ経由
#   PGHOST を設定すると、ホストの psql / pg_dump / pg_restore を直接使う(復元の検証などに使う)
set -euo pipefail

: "${POSTGRES_DB:=productiontracker}"
: "${POSTGRES_USER:=productiontracker}"

if [ -n "${PGHOST:-}" ]; then
  export PGUSER="${PGUSER:-$POSTGRES_USER}"
  run_pg() { "$@"; }
else
  run_pg() { docker compose exec -T db "$@"; }
fi

# 主要テーブルの件数(バックアップ時と復元後で突き合わせる)
COUNT_SQL="SELECT 'project', count(*) FROM tracker_project UNION ALL
SELECT 'entity', count(*) FROM tracker_entity UNION ALL
SELECT 'task', count(*) FROM tracker_task UNION ALL
SELECT 'version', count(*) FROM tracker_version UNION ALL
SELECT 'note', count(*) FROM tracker_note UNION ALL
SELECT 'quality_report', count(*) FROM tracker_qualityreport UNION ALL
SELECT 'visual_result', count(*) FROM tracker_visualresult ORDER BY 1"

row_counts() { # $1 = DB 名
  run_pg psql -U "$POSTGRES_USER" -d "$1" -At -F ' ' -c "$COUNT_SQL"
}
