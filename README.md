# Vaultwarden 自动备份脚本

本项目用于自动化备份 Vaultwarden 密码管理服务的数据，支持加密、云端存储、备份轮换和 Telegram 通知。
>  README.md是由Copilot AI 生成的，可能包含一些不准确或不完整的信息，请根据实际情况进行调整和补充。如果遇到情况请提交 Issue 或 PR 进行修正，万分感谢！

---

## 项目背景
Vaultwarden 是 Bitwarden 的轻量级开源实现，常用于自建密码管理服务。数据安全至关重要，定期自动备份能有效防止数据丢失。本脚本实现了备份、加密、上传、轮换和通知的全流程自动化。

## 功能亮点
- 自动备份 Vaultwarden 的数据库、配置文件、私钥和附件目录
- 使用 openssl 强加密备份文件，保障数据安全
- 上传加密备份至 Cloudflare R2 对象存储
- 自动轮换旧备份，保留指定数量，节省存储空间
- 备份失败时自动通过 Telegram 推送通知
- 支持多平台（Windows/Linux）

---

## 环境准备

### 1. 克隆或下载项目
将本项目代码克隆或下载zip:
   ```
   git clone https://github.com/你的仓库/vaultwarden_backup.git
   ```

### 2. 配置环境变量
1. 将 `.env-ex` 文件重命名为 `backup.env`，并根据实际情况填写各项配置。
2. 各项配置说明：
   - `R2_ACCESS_KEY_ID`：Cloudflare R2 的 Access Key
   - `R2_SECRET_ACCESS_KEY`：Cloudflare R2 的 Secret Key
   - `R2_ACCOUNT_ID`：Cloudflare R2 的账号 ID
   - `R2_BUCKET_NAME`：R2 存储桶名称
   - `R2_REGION`：R2 区域（通常填 auto）
   - `BACKUP_SOURCE_DIR`：Vaultwarden 数据目录（如 `/opt/vaultwarden/data` 或 `C:\vaultwarden\data`）
   - `BACKUP_TEMP_FILE`：临时 tar 文件路径（如 `/tmp/vaultwarden-backup.tar.gz` 或 `C:\temp\vaultwarden-backup.tar.gz`）
   - `BACKUP_ENCRYPTED_FILE`：加密后文件路径（如 `/tmp/vaultwarden-backup.tar.gz.enc`）
   - `ENCRYPT_PASSWORD`：备份加密密码（请妥善保存）
   - `SLOT_COUNT`：保留的备份数量（如 3）
   - `BACKUP_PREFIX`：备份文件前缀（如 `back-vault-s`）
   - `TELEGRAM_BOT_TOKEN`：Telegram Bot Token（可选）
   - `TELEGRAM_CHAT_ID`：Telegram Chat ID（可选）

3. 配置示例：
```
R2_ACCESS_KEY_ID=xxxxxx
R2_SECRET_ACCESS_KEY=xxxxxx
R2_ACCOUNT_ID=xxxxxx
R2_BUCKET_NAME=vault-backup
R2_REGION=auto
BACKUP_SOURCE_DIR=/opt/vaultwarden/data
BACKUP_TEMP_FILE=/tmp/vaultwarden-backup.tar.gz
BACKUP_ENCRYPTED_FILE=/tmp/vaultwarden-backup.tar.gz.enc
ENCRYPT_PASSWORD=你的强密码
SLOT_COUNT=3
BACKUP_PREFIX=back-vault-s
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789
```

---

## 依赖安装

### Python 依赖
请确保已安装 Python 3.7 及以上版本。

#### 方式一：使用 requirements.txt
```
pip install -r requirements.txt
```

#### 方式二：手动安装
```
pip install boto3 python-dotenv requests
```

### 系统依赖
- Windows：请确保 `sqlite3.exe` 和 `openssl.exe` 已加入环境变量（可用 scoop/choco 安装）
- Linux：
```
sudo apt install sqlite3 openssl
```

---

## 备份流程详解
1. 备份数据库：使用 sqlite3 的 .backup 命令生成安全副本
2. 打包数据：将数据库、配置文件、私钥和附件目录打包为 tar.gz
3. 加密备份：用 openssl AES-256-CBC 加密备份文件
4. 上传备份：将加密文件上传至 Cloudflare R2
5. 轮换备份：自动删除超出 SLOT_COUNT 的旧备份
6. 清理临时文件：删除本地临时文件
7. 通知推送：如有异常，自动推送 Telegram 消息

---

## 运行方法
在项目目录下执行：
```
python backup.py
```

如需定时自动运行，可结合系统计划任务：
- Windows：任务计划程序
- Linux：crontab

---

## 数据安全说明
- 备份文件采用 AES-256-CBC 加密，密码由 ENCRYPT_PASSWORD 指定
- 加密密码请妥善保存，遗失将无法恢复备份内容
- 云端存储采用 Cloudflare R2，需正确配置密钥

---

## Telegram 通知配置
如需异常通知，请在 Telegram 创建 Bot 并获取 Token，查找你的 Chat ID 并填写到 `backup.env`。

- Bot 创建教程：https://core.telegram.org/bots#creating-a-new-bot
- Chat ID 获取方法：可用 @userinfobot 查询

---

## 备份轮换机制
- 每次备份后自动检查云端备份数量，超出 SLOT_COUNT 时自动删除最旧的备份
- 备份文件命名格式：`{BACKUP_PREFIX}{日期时间}.tar.gz.enc`

---

## 常见问题与故障排查
- **依赖未安装**：请检查 Python 包和系统工具是否安装齐全
- **权限问题**：请确保数据目录和临时文件路径有读写权限
- **上传失败**：检查 R2 配置和网络连接
- **加密失败**：确认 openssl 命令可用，密码无特殊字符
- **Telegram 未推送**：检查 Bot Token 和 Chat ID 是否正确

---

## FAQ
- Q: 如何恢复备份？
  A: 下载加密备份文件，使用 openssl 解密后解包 tar 文件即可。
- Q: 可以只备份数据库吗？
  A: 可自行修改 backup.py，只保留数据库相关打包逻辑。
- Q: 支持多平台吗？
  A: 支持 Windows 和 Linux，MacOS 亦可。

---

## 贡献与反馈
如有建议、问题或需求，欢迎提交 Issue 或 PR。

---

> 本项目旨在简化 Vaultwarden 的备份流程，提升数据安全性。感谢您的使用！
