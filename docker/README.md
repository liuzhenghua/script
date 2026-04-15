# Docker

用于本地快速启动 `MySQL` 和 `PostgreSQL`，现在按数据库拆成独立目录。

## 目录结构

- `docker/mysql/`
- `docker/postgres/`

每个目录下都包含：

- `docker-compose.yml`
- `.env.example`
- `data/`
- `init/`

## MySQL

```bash
cd docker/mysql
cp .env.example .env
docker compose up -d
```

查看日志：

```bash
docker compose logs -f
```

停止：

```bash
docker compose down
```

默认连接：`127.0.0.1:3306`

数据目录：`docker/mysql/data/`

## PostgreSQL

```bash
cd docker/postgres
cp .env.example .env
docker compose up -d
```

查看日志：

```bash
docker compose logs -f
```

停止：

```bash
docker compose down
```

默认连接：`127.0.0.1:5432`

数据目录：`docker/postgres/data/`

## 初始化脚本

- MySQL 初始化 SQL 放在 `docker/mysql/init/`
- PostgreSQL 初始化 SQL 放在 `docker/postgres/init/`

容器首次初始化时会自动执行这些目录下的脚本。
