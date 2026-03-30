#!/bin/bash

# ==========================================
# Desc: 定期解析域名并更新 /etc/hosts
# 前置确认脚本：mkdir /usr/local/libexec
# 拷贝文件(需要root): cp update_hosts.sh /usr/local/libexec/ && cp plist/local.hosts-file-update.plist /Library/LaunchDaemons/
# 安装任务：launchctl load /Library/LaunchDaemons/local.hosts-file-update.plist
# ==========================================
DOMAINS=(
  "test.cvpn-endpoint-04a43651f28c7c9b7.prod.clientvpn.eu-west-2.amazonaws.com"
  "prod-apollo-mexico-nlb-676017c508fa9356.elb.mx-central-1.amazonaws.com"
  "prod-com-oversea-nlb-d1b24572442e75db.elb.mx-central-1.amazonaws.com"
  "prod-dubboadmin-nlb-d7280a2a2a70f46c.elb.mx-central-1.amazonaws.com"
  "prod-scheduler-mexico-3561285d990727be.elb.mx-central-1.amazonaws.com"
  "prod-cas-mexico-nlb-b7b4e708c7281721.elb.mx-central-1.amazonaws.com"
  "prod-rocketmq-console-nlb-2ed9927af387dca1.elb.mx-central-1.amazonaws.com"
  "prod-warehouse-oversea-nlb-90613baefa54898e.elb.mx-central-1.amazonaws.com"
)
DNS="8.8.8.8"
HOSTS_FILE="/etc/hosts"
TMP_FILE="/tmp/hosts.tmp"
CHANGED=0

# 复制原 hosts
cp "$HOSTS_FILE" "$TMP_FILE"
# 验证是否为有效 IP 地址
is_valid_ip() {
    local ip=$1
    if [[ "$ip" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        return 0
    fi
    return 1
}
for domain in "${DOMAINS[@]}"; do
    # 用 dig 获取第一个 IP
    ip=$(/usr/bin/dig +short "$domain" @"$DNS" | /usr/bin/head -n1)
    # 验证是否为有效 IP，避免 dig 失败时更新错误记录
    if is_valid_ip "$ip"; then
        # 取旧 IP（如果存在）
        old_ip=$(/usr/bin/grep "[[:space:]]$domain\$" "$HOSTS_FILE" | /usr/bin/awk '{print $1}')
        if [ "$ip" != "$old_ip" ]; then
            echo "Updating $domain: $old_ip -> $ip"
            # 删除旧记录
            /usr/bin/sed -i '' "/[[:space:]]$domain$/d" "$TMP_FILE"
            # 添加新记录
            echo "$ip $domain" >> "$TMP_FILE"
            CHANGED=1
        fi
    else
        echo "Dig failed for $domain, result: '$ip'"
    fi
done

# 只有变化才覆盖
if [ "$CHANGED" -eq 1 ]; then
    /bin/cp "$TMP_FILE" "$HOSTS_FILE"
    # 刷新 DNS 缓存
    /usr/bin/dscacheutil -flushcache
    /usr/bin/killall -HUP mDNSResponder
    echo "Hosts updated at $(date)"
else
    echo "No changes at $(date)"
fi