# 同步最近 7 天的 agent_sessions 数据
#
# 源路径: /mnt/data/agent_sessions/<user>/<coding_agent>/yyyy-MM-dd/xxx
# 目标路径: /data/agent_sessions/<user>/<coding_agent>/yyyy-MM-dd/xxx
# 排除: .tmp_uploads 目录
#
# crontab 配置 (每5分钟执行一次，使用 flock 防止并发):
# */5 * * * * flock -n /var/run/agent_sessions_rsync.lock /usr/local/libexec/rsync_7_days_agent_sessions.sh

LOG=/var/log/agent_sessions_rsync.log

start=$(date +%s)
echo "$(date '+%F %T'): agent session rsync trigger." >> "$LOG"

# 预计算最近 7 天的日期
days=()
for i in $(seq 0 7); do
  days+=($(date -d "$i days ago" +%F))
done

for dir in /mnt/data/agent_sessions/*/*/; do
  for day in "${days[@]}"; do
    [ -d "$dir$day" ] || continue

    rel=${dir#/mnt/data/agent_sessions/}${day}
    mkdir -p "/data/agent_sessions/$rel"

    rsync -a --delete \
      --exclude=".tmp_uploads" \
      "$dir$day/" "/data/agent_sessions/$rel/" >> "$LOG" 2>&1
  done
done

end=$(date +%s)
echo "$(date '+%F %T'): agent session rsync finished, cost $((end-start))s." >> "$LOG"
