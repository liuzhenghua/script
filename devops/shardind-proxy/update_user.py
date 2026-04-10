"""
pip install kazoo
"""
from kazoo.client import KazooClient

# 连接到 Zookeeper
zk = KazooClient(hosts="$IP1:2181,$IP2:2181,$IP3:2181")
zk.start()

# 要设置的 key
znode_path = "/shardingsphere-proxy/rules/authority/versions/0"

# 要设置的值，包含换行符
value = """users:
  - user: root@%
    password: $PASSWORD
  - user: demo@%
    password: $PASSWORD
privilege:
  type: DATABASE_PERMITTED
  props:
    user-database-mappings: >
      root@%=*,
      demo@%=demo_dev,demo@%=demo_stg
"""

# 设置 Zookeeper znode 的值
zk.set(znode_path, value.encode('utf-8'))

# 关闭连接
zk.stop()
