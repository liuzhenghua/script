#!/bin/bash

# =============================
# 🧠 重置路由表（将某个目标IP的流量都转发到utun上，再通过tun2socks发给clash）
# 安装tun2socks(解压到/usr/local/bin): https://github.com/xjasonlyu/tun2socks/
# tun2socks --device utun233 --proxy socks5://127.0.0.1:7897
# =============================
INTERFACE="utun233"
DOMAIN="test.cvpn-endpoint-04a43651f28c7c9b7.prod.clientvpn.eu-west-2.amazonaws.com"
HOSTS_FILE="/etc/hosts"
#OVPN_CONFIG="/Users/liuzhenghua/.config/AWSVPNClient/OpenVpnConfigs/uk-fixip"

echo "=============================="
echo "🧠 Reset routing on $INTERFACE"
echo "=============================="

# 1. 从 hosts 获取 IP（唯一真源）
REAL_IP=$(grep -E "[[:space:]]$DOMAIN([[:space:]]|$)" "$HOSTS_FILE" | awk '{print $1}' | tail -n 1)

if [ -z "$REAL_IP" ]; then
    echo "❌ IP not found in hosts"
    exit 1
fi

echo "✅ Hosts IP: $REAL_IP"

# 2. 修改 OVPN 配置文件中的 remote 行
#echo "📝 Updating OVPN config: $OVPN_CONFIG"
#if [ -f "$OVPN_CONFIG" ]; then
#    # 替换 remote 开头的行为新的 remote $REAL_IP 443
#    sed -i '' "s/^remote.*/remote $REAL_IP 443/" "$OVPN_CONFIG"
#    echo "✅ OVPN config updated: remote $REAL_IP 443"
#else
#    echo "⚠️ OVPN config file not found: $OVPN_CONFIG"
#fi

# 3. 只删除 "host route"，不动 interface peer（关键点）
#echo "🧹 Cleaning host routes bound to $INTERFACE ..."
#
#netstat -rn -f inet | awk -v iface="$INTERFACE" '$2 == iface && $1 ~ /^[0-9]+\./ { print $1 }' | while read ip; do
#    echo "  deleting route: $ip"
#    sudo route delete -host "$ip" 2>/dev/null
#done

# 4. 重新绑定唯一目标路由
echo "➕ Adding fresh route to $REAL_IP via $INTERFACE"
sudo route add -host "$REAL_IP" -interface "$INTERFACE"

echo "🎉 $INTERFACE reset completed"