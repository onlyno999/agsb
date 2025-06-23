#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
import platform
import urllib.request
import shutil
from pathlib import Path
from datetime import datetime
import argparse

INSTALL_DIR = Path.home() / ".socks5_proxy"
SB_BIN = INSTALL_DIR / "sing-box"
SB_CONF = INSTALL_DIR / "sb.json"
SB_PID = INSTALL_DIR / "sb.pid"
SB_LOG = INSTALL_DIR / "sb.log"

DEFAULT_PORT = 10808

def parse_args():
    parser = argparse.ArgumentParser(description="纯 SOCKS5 代理一键脚本")
    parser.add_argument("action", nargs="?", default="install", choices=["install", "status", "uninstall"])
    parser.add_argument("--port", "-p", type=int, help="SOCKS5 监听端口 (默认 10808)")
    return parser.parse_args()

def download_sing_box():
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = "amd64"
    if "arm64" in machine or "aarch64" in machine:
        arch = "arm64"
    elif "armv7" in machine:
        arch = "armv7"
    version = "1.9.0-beta.11"
    name = f"sing-box-{version}-linux-{arch}"
    url = f"https://github.com/SagerNet/sing-box/releases/download/v{version}/{name}.tar.gz"
    tar = INSTALL_DIR / "sb.tgz"
    print(f"下载 {url}")
    os.system(f"curl -L '{url}' -o '{tar}'")
    os.system(f"tar -xzf '{tar}' -C '{INSTALL_DIR}'")
    os.system(f"mv '{INSTALL_DIR}/{name}/sing-box' '{SB_BIN}'")
    os.system(f"chmod +x '{SB_BIN}'")
    shutil.rmtree(INSTALL_DIR / name)
    tar.unlink()

def create_config(port):
    config = {
        "log": {"level": "info"},
        "inbounds": [{
            "type": "socks",
            "listen": "0.0.0.0",
            "listen_port": port,
            "sniff": True
        }],
        "outbounds": [{"type": "direct"}]
    }
    with open(SB_CONF, "w") as f:
        json.dump(config, f, indent=2)

def get_public_ip():
    try:
        return urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode().strip()
    except:
        return "未知"

def start_sing_box():
    cmd = f"{SB_BIN} run -c {SB_CONF} > {SB_LOG} 2>&1 & echo $! > {SB_PID}"
    os.system(cmd)

def install(args):
    port = args.port or DEFAULT_PORT
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    download_sing_box()
    create_config(port)
    start_sing_box()
    pub_ip = get_public_ip()
    print(f"\n🎉 SOCKS5 已启动")
    print(f"本地地址: socks5://127.0.0.1:{port}")
    print(f"公网地址: socks5://{pub_ip}:{port}\n")

def status():
    if SB_PID.exists():
        pid = SB_PID.read_text().strip()
        if pid and os.path.exists(f"/proc/{pid}"):
            print(f"SOCKS5 正在运行 (PID {pid})")
        else:
            print("SOCKS5 未运行")
    else:
        print("SOCKS5 未安装或未运行")

def uninstall():
    if SB_PID.exists():
        pid = SB_PID.read_text().strip()
        if pid:
            os.system(f"kill {pid}")
            print("已停止 SOCKS5 进程")
    if INSTALL_DIR.exists():
        shutil.rmtree(INSTALL_DIR)
        print("已删除安装目录")

def main():
    args = parse_args()
    if args.action == "install":
        install(args)
    elif args.action == "status":
        status()
    elif args.action == "uninstall":
        uninstall()

if __name__ == "__main__":
    main()
