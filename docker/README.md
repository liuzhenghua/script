# Docker

用于本地快速启动 `MySQL`、`PostgreSQL`、`Redis` 和 `SeekDB`，现在按数据库拆成独立目录。

## 目录结构

- `docker/mysql/`
- `docker/postgres/`
- `docker/redis/`
- `docker/seekdb/`

每个目录下都包含：

- `docker-compose.yml`
- `.env.example`
- `data/`
- `init/`

## 启动

```bash
cd docker

# MySQL
cp mysql/.env.example mysql/.env
docker compose -f mysql/docker-compose.yml up -d

# PostgreSQL
cp postgres/.env.example postgres/.env
docker compose -f postgres/docker-compose.yml up -d

# SeekDB
cp seekdb/.env.example seekdb/.env
docker compose -f seekdb/docker-compose.yml up -d

# Redis
cp redis/.env.example redis/.env
docker compose -f redis/docker-compose.yml up -d
```

## 查看日志

```bash
docker compose -f docker/mysql/docker-compose.yml logs -f
docker compose -f docker/postgres/docker-compose.yml logs -f
docker compose -f docker/seekdb/docker-compose.yml logs -f
docker compose -f docker/redis/docker-compose.yml logs -f
```

## 停止

```bash
docker compose -f docker/mysql/docker-compose.yml down
docker compose -f docker/postgres/docker-compose.yml down
docker compose -f docker/seekdb/docker-compose.yml down
docker compose -f docker/redis/docker-compose.yml down
```

## 连接信息

| 数据库     | 默认连接          | 数据目录               | 备注                        |
| ---------- | ----------------- | ---------------------- | --------------------------- |
| MySQL      | `127.0.0.1:3306`  | `docker/mysql/data/`   |                             |
| PostgreSQL | `127.0.0.1:5432`  | `docker/postgres/data/`|                             |
| Redis      | `127.0.0.1:6379`  | `docker/redis/data/`   | 默认密码: `app123456`        |
| SeekDB     | `127.0.0.1:2881`  | `docker/seekdb/data/`  | OBShell 控制台: `127.0.0.1:2886` |

## 初始化脚本

- MySQL 初始化 SQL 放在 `docker/mysql/init/`
- PostgreSQL 初始化 SQL 放在 `docker/postgres/init/`
- SeekDB 初始化 SQL 放在 `docker/seekdb/init/`

容器首次初始化时会自动执行这些目录下的脚本。
