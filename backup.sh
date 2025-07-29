#!/bin/bash
set -e

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 读取配置
source ./backup.env

echo "[INFO] 停止 Vaultwarden 容器"
cd "$COMPOSE_DIR"
docker compose stop vaultwarden

echo "[INFO] 运行备份 Python 脚本"
python3 backup.py

echo "[INFO] 启动 Vaultwarden 容器"
docker compose start vaultwarden

echo "[INFO] 备份完成"
