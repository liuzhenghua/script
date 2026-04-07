# Nginx 安装指南

## macOS

### Homebrew（推荐）

```bash
brew install nginx
brew services start nginx
brew services stop nginx
brew services restart nginx
nginx -t && nginx -v
```

验证：`curl http://localhost:8080`

路径：配置 `/usr/local/etc/nginx/` | 日志 `/usr/local/var/log/nginx/` | 文档根 `/usr/local/var/www/`

---

## Linux

### Ubuntu / Debian

```bash
sudo apt update && sudo apt install nginx
sudo systemctl start nginx && sudo systemctl enable nginx
sudo nginx -t
```

### CentOS / RHEL / Rocky

```bash
# CentOS 7
sudo yum install epel-release
# CentOS 8+ / Rocky
sudo dnf install nginx
sudo systemctl start nginx && sudo systemctl enable nginx
sudo nginx -t
```

验证：`curl http://localhost`

路径：配置 `/etc/nginx/` | 日志 `/var/log/nginx/` | 文档根 `/usr/share/nginx/html/`

---

## Docker

### 快速启动

```bash
docker run -d --name nginx -p 80:80 nginx:latest
```

### 自定义配置

```bash
mkdir -p ~/nginx/{conf.d,logs,html}
docker run -d --name nginx -p 80:80 -p 443:443 \
  -v ~/nginx/conf.d:/etc/nginx/conf.d \
  -v ~/nginx/logs:/var/log/nginx \
  -v ~/nginx/html:/usr/share/nginx/html \
  nginx:latest
```

### Docker Compose

```yaml
version: '3'
services:
  nginx:
    image: nginx:latest
    container_name: nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./conf.d:/etc/nginx/conf.d
      - ./logs:/var/log/nginx
      - ./html:/usr/share/nginx/html
    restart: unless-stopped
```

```bash
docker-compose up -d
docker-compose logs -f nginx
docker-compose down
```

---

## proxy_http 配置示例

### HTTP 反向代理

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### WebSocket 反向代理

```nginx
server {
    listen 80;
    server_name example.com;

    location /ws {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}
```

### HTTPS 反向代理

```nginx
server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 负载均衡

```nginx
upstream backend {
    least_conn;
    server 127.0.0.1:8080 weight=3;
    server 127.0.0.1:8081 weight=2;
    server 127.0.0.1:8082 weight=1;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 路径转发

```nginx
server {
    listen 80;
    server_name example.com;

    location /api/ {
        proxy_pass http://127.0.0.1:3000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /blog/ {
        proxy_pass http://127.0.0.1:4000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 常用 proxy_set_header

| 指令 | 说明 |
|------|------|
| `Host $host` | 传递原始请求 Host |
| `X-Real-IP $remote_addr` | 传递客户端真实 IP |
| `X-Forwarded-For` | 代理链 IP 列表 |
| `X-Forwarded-Proto` | 原始协议 (http/https) |
| `Upgrade $http_upgrade` | WebSocket 升级 |
| `Connection "upgrade"` | WebSocket 连接升级 |

---

## 常用命令

```bash
nginx -t              # 测试配置
nginx -s reload      # 平滑重载
nginx -s stop        # 平滑停止
ps aux | grep nginx  # 查看进程
lsof -i :80           # 检查端口
```
