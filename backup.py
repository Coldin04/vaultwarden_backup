import os
import tarfile
import boto3
import datetime
import hashlib
import shutil
import requests
from dotenv import load_dotenv
from subprocess import run

# 加载配置
load_dotenv('./backup.env')  # 或 '.env'，看你放哪

# 环境变量
access_key = os.getenv('R2_ACCESS_KEY_ID')
secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
account_id = os.getenv('R2_ACCOUNT_ID')
bucket = os.getenv('R2_BUCKET_NAME')
region = os.getenv('R2_REGION', 'auto')

source_dir = os.getenv('BACKUP_SOURCE_DIR')
tar_path = os.getenv('BACKUP_TEMP_FILE')
enc_path = os.getenv('BACKUP_ENCRYPTED_FILE')
enc_password = os.getenv('ENCRYPT_PASSWORD')

slot_count = int(os.getenv('SLOT_COUNT', 3))
backup_prefix = os.getenv('BACKUP_PREFIX', 'back-vault-s')

# 创建 R2 客户端
session = boto3.session.Session()
client = session.client(
    service_name='s3',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
    region_name=region,
)

# 发送 Telegram 消息
def send_telegram_message(text):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id:
        print('[!] 未配置 Telegram 推送，无法发送通知')
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f'[!] Telegram 推送失败: {e}')

"""
def tar_backup():
    print('[*] 打包数据...')
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
"""
def sqlite_backup():
    print('[*] 使用 sqlite3 .backup 命令备份数据库...')
    db_file = os.path.join(source_dir, 'db.sqlite3')
    backup_db_file = os.path.join(source_dir, 'db-backup.sqlite3')
    if os.path.exists(db_file):
        cmd = [
            "sqlite3", db_file,
            f".backup '{backup_db_file}'"
        ]
        run(cmd, check=True)
    else:
        print('[!] 未找到数据库文件，跳过数据库备份')
    return backup_db_file

def tar_backup():
    print('[*] 只备份必要数据...')
    backup_db_file = sqlite_backup()
    with tarfile.open(tar_path, "w:gz") as tar:
        # 主数据库
        db_file = os.path.join(source_dir, 'db.sqlite3')
        if os.path.exists(db_file):
            tar.add(db_file, arcname='db.sqlite3')
        # 配置文件
        config_file = os.path.join(source_dir, 'config.json')
        if os.path.exists(config_file):
            tar.add(config_file, arcname='config.json')
        # 私钥
        rsa_file = os.path.join(source_dir, 'rsa_key.pem')
        if os.path.exists(rsa_file):
            tar.add(rsa_file, arcname='rsa_key.pem')
        # 附件目录（如有需要）
        attachments_dir = os.path.join(source_dir, 'attachments')
        if os.path.exists(attachments_dir):
            tar.add(attachments_dir, arcname='attachments')
    if os.path.exists(backup_db_file):
        os.remove(backup_db_file)

def encrypt_backup():
    print('[*] 加密备份...')
    cmd = [
        "openssl", "enc", "-aes-256-cbc", "-salt", "-pbkdf2",
        "-in", tar_path,
        "-out", enc_path,
        "-k", enc_password
    ]
    run(cmd, check=True)

def upload_backup():
    now = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    object_key = f"{backup_prefix}{now}.tar.gz.enc"
    print(f'[*] 上传备份 {object_key} ...')
    with open(enc_path, 'rb') as f:
        client.upload_fileobj(f, bucket, object_key)
    return object_key

def rotate_backups():
    print('[*] 检查并轮换旧备份...')
    res = client.list_objects_v2(Bucket=bucket, Prefix=backup_prefix)
    if 'Contents' not in res:
        print('[+] 无需轮换，当前仅有一个备份')
        return

    backups = sorted(
        [obj['Key'] for obj in res['Contents']],
        key=lambda k: k
    )
    if len(backups) <= slot_count:
        print(f'[+] 当前备份数 {len(backups)} 未超过 {slot_count}，无需删除')
        return

    to_delete = backups[0:len(backups)-slot_count]
    for key in to_delete:
        print(f'[-] 删除过旧备份 {key}')
        client.delete_object(Bucket=bucket, Key=key)

def cleanup():
    print('[*] 清理临时文件')
    for f in [tar_path, enc_path]:
        if os.path.exists(f):
            os.remove(f)

def main():
    try:
        tar_backup()
        encrypt_backup()
        upload_backup()
        rotate_backups()
        cleanup()
        print('[✓] 所有备份流程完成')
    except Exception as e:
        err_msg = f'[!] 备份流程出错: {e}'
        print(err_msg)
        send_telegram_message(err_msg)
        
if __name__ == "__main__":
    main()
