#!/usr/bin/env python3
import os
import subprocess
import sys
import json
import urllib.request
import shutil

# 基础变量
SOCKSU = os.getenv('SOCKSU', 'onezun')
SOCKSP = os.getenv('SOCKSP', 'momomemo')
STCP = os.getenv('STCP', '1080')
SUDP = os.getenv('SUDP', '1080')
DOMAIN = os.getenv('DOMAIN', '')

USERNAME = os.popen('whoami').read().strip().lower()
HOSTNAME = os.popen('hostname').read().strip()

# 自动识别域名
if not DOMAIN:
    if 'ct8' in HOSTNAME:
        CURRENT_DOMAIN = f"{USERNAME}.ct8.pl"
    elif 'hostuno' in HOSTNAME:
        CURRENT_DOMAIN = f"{USERNAME}.useruno.com"
    else:
        CURRENT_DOMAIN = f"{USERNAME}.serv00.net"
else:
    CURRENT_DOMAIN = DOMAIN

def green(msg):
    print(f"\033[1;32m{msg}\033[0m")

def purple(msg):
    print(f"\033[1;35m{msg}\033[0m")

# 创建 devil 面板 nodejs 站点
def check_website():
    try:
        result = subprocess.check_output("devil www list", shell=True, text=True)
        found = False
        for line in result.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == CURRENT_DOMAIN and parts[1] == 'nodejs':
                found = True
                break
        if found:
            green(f"已存在 {CURRENT_DOMAIN} 的 nodejs 站点\n")
        else:
            subprocess.run(f"devil www del {CURRENT_DOMAIN}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(f"devil www add {CURRENT_DOMAIN} nodejs /usr/local/bin/node18", shell=True, stdout=subprocess.DEVNULL)
            green(f"已创建 {CURRENT_DOMAIN} nodejs 站点\n")
    except subprocess.CalledProcessError:
        print("devil 面板命令执行出错，请检查 devil 是否正常。")
        sys.exit(1)

check_website()

SITE_PATH = os.path.expanduser(f"~/domains/{CURRENT_DOMAIN}/public_nodejs/public")
os.makedirs(SITE_PATH, exist_ok=True)
os.chdir(SITE_PATH)

# 下载 SOCKS5 可执行文件
SS5_BIN = os.path.join(SITE_PATH, "ss5")
if not os.path.isfile(SS5_BIN):
    url = "https://github.com/Neomanbeta/00-socks5/releases/download/freebsd-amd64/ss5"
    with urllib.request.urlopen(url) as response, open("ss5", 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    os.chmod("ss5", 0o755)

# 写入 ss5 配置
ss5_config = {
    "ListenPort": int(STCP),
    "TCPListen": "",
    "UDPListen": f"127.0.0.1:{SUDP}",
    "UDPAdvertisedIP": "",
    "UserName": SOCKSU,
    "Password": SOCKSP,
    "UDPTimout": 60,
    "TCPTimeout": 60,
    "LogLevel": "error"
}
with open("ss5.json", "w") as f:
    json.dump(ss5_config, f, indent=2)

# 创建默认 index.html 保活
with open("index.html", "w") as f:
    f.write("""<!DOCTYPE html>
<html>
  <head><meta charset="utf-8"><title>SOCKS5 Proxy</title></head>
  <body><h2>SOCKS5 服务运行中 - 保活成功</h2></body>
</html>
""")

# 重启 devil 网站
subprocess.run(f"devil www restart {CURRENT_DOMAIN}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 判断是否已有 ss5 在运行
def is_ss5_running():
    try:
        result = subprocess.check_output("pgrep -f 'ss5 -c ss5.json'", shell=True)
        return bool(result.strip())
    except subprocess.CalledProcessError:
        return False

if is_ss5_running():
    purple("检测到 ss5 已在运行，跳过启动。")
else:
    subprocess.Popen([SS5_BIN, "-c", "ss5.json"])
    green("ss5 启动成功")

# 输出信息
try:
    with urllib.request.urlopen('http://ifconfig.me/ip') as response:
        ip = response.read().decode().strip()
except:
    ip = "未知IP"

print(f"\n\033[1;32mSOCKS5 已绑定在 public_nodejs/public 保活网页上\033[0m")
print(f"\033[1;32m主页：http://{CURRENT_DOMAIN}/ \033[0m")
print(f"\033[1;32msocks5://{SOCKSU}:{SOCKSP}@{ip}:{STCP}#SOCKS5_PROXY\033[0m\n")
