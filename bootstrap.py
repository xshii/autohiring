#!/usr/bin/env python3
"""项目初始化脚本 - 跨平台支持"""

import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request


def run(cmd, check=True, capture=False):
    """执行命令"""
    print(f"  > {cmd}")
    if capture:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    else:
        result = subprocess.run(cmd, shell=True, check=check)
        return result.returncode == 0


def get_chrome_version():
    """获取本地 Chrome 版本"""
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            cmd = '"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version'
            output = run(cmd, check=False, capture=True)
        elif system == "Windows":
            cmd = 'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version'
            output = run(cmd, check=False, capture=True)
            if output:
                match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output)
                return match.group(1) if match else None
        else:  # Linux
            for browser in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]:
                output = run(f"{browser} --version", check=False, capture=True)
                if output:
                    break

        if output:
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output)
            return match.group(1) if match else None
    except Exception as e:
        print(f"  获取 Chrome 版本失败: {e}")

    return None


def get_chromedriver_url(chrome_version):
    """获取匹配的 ChromeDriver 下载链接"""
    system = platform.system()
    machine = platform.machine().lower()

    # 确定平台标识
    if system == "Darwin":
        platform_name = "mac-arm64" if machine == "arm64" else "mac-x64"
    elif system == "Windows":
        platform_name = "win64" if "64" in machine or machine == "amd64" else "win32"
    else:  # Linux
        platform_name = "linux64"

    # 获取主版本号
    major_version = chrome_version.split(".")[0]

    try:
        # 使用 Chrome for Testing API
        api_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        print(f"  获取 ChromeDriver 版本信息...")

        req = Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

        # 找到匹配的版本
        matching_versions = [
            v for v in data["versions"]
            if v["version"].startswith(f"{major_version}.")
            and "chromedriver" in v.get("downloads", {})
        ]

        if not matching_versions:
            print(f"  未找到匹配 Chrome {major_version} 的 ChromeDriver")
            return None

        # 使用最新的匹配版本
        latest = matching_versions[-1]
        driver_downloads = latest["downloads"]["chromedriver"]

        for download in driver_downloads:
            if download["platform"] == platform_name:
                return download["url"], latest["version"]

    except Exception as e:
        print(f"  获取 ChromeDriver 下载链接失败: {e}")

    return None


def download_chromedriver(url, version, dest_dir):
    """下载并解压 ChromeDriver"""
    system = platform.system()
    driver_name = "chromedriver.exe" if system == "Windows" else "chromedriver"
    dest_path = dest_dir / driver_name

    if dest_path.exists():
        print(f"  ChromeDriver 已存在: {dest_path}")
        return dest_path

    try:
        print(f"  下载 ChromeDriver {version}...")
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=60) as response:
            zip_data = response.read()

        print(f"  解压 ChromeDriver...")
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            # 找到 chromedriver 文件
            for name in zf.namelist():
                if name.endswith(driver_name):
                    # 解压到目标目录
                    with zf.open(name) as src:
                        dest_path.write_bytes(src.read())
                    break

        # 设置可执行权限 (Unix)
        if system != "Windows":
            dest_path.chmod(0o755)

        print(f"  ChromeDriver 已安装: {dest_path}")
        return dest_path

    except Exception as e:
        print(f"  下载 ChromeDriver 失败: {e}")
        return None


def setup_chromedriver(project_root):
    """设置 ChromeDriver"""
    print("\n检测 Chrome 版本...")
    chrome_version = get_chrome_version()

    if not chrome_version:
        print("  未检测到 Chrome，跳过 ChromeDriver 安装")
        print("  请手动安装 Chrome 浏览器")
        return None

    print(f"  Chrome 版本: {chrome_version}")

    # 获取下载链接
    result = get_chromedriver_url(chrome_version)
    if not result:
        return None

    url, driver_version = result
    print(f"  匹配的 ChromeDriver 版本: {driver_version}")

    # 下载目录
    drivers_dir = project_root / "drivers"
    drivers_dir.mkdir(exist_ok=True)

    return download_chromedriver(url, driver_version, drivers_dir)


def main():
    print("=== AutoHiring 项目初始化 ===\n")

    project_root = Path(__file__).parent
    os.chdir(project_root)

    # 检查 Python 版本
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    if version < (3, 9):
        print("错误: 需要 Python 3.9 或更高版本")
        sys.exit(1)

    # 虚拟环境路径
    venv_path = project_root / ".venv"

    # 确定 Python 和 pip 路径
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
        activate_cmd = ".venv\\Scripts\\activate"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
        activate_cmd = "source .venv/bin/activate"

    # 创建虚拟环境
    if not venv_path.exists():
        print("\n创建虚拟环境...")
        run(f"{sys.executable} -m venv .venv")
    else:
        print("\n虚拟环境已存在")

    # 升级 pip
    print("\n升级 pip...")
    run(f"{pip_exe} install --upgrade pip -q")

    # 安装项目依赖
    print("\n安装项目依赖...")
    run(f"{pip_exe} install -e . -q")

    # 安装可选依赖
    print("\n安装 edge-tts...")
    run(f"{pip_exe} install edge-tts -q")

    # 安装 selenium
    print("\n安装 selenium...")
    run(f"{pip_exe} install selenium -q")

    # 设置 ChromeDriver
    chromedriver_path = setup_chromedriver(project_root)

    print("\n" + "=" * 40)
    print("初始化完成!")
    print("=" * 40)
    print(f"\n使用方法:")
    print(f"  {activate_cmd}    # 激活虚拟环境")
    print(f"  autohiring --help            # 查看帮助")
    print(f"\n可用命令:")
    print(f"  autohiring phone lookup <号码>    # 查询电话归属地")
    print(f"  autohiring scraper start          # 启动爬虫服务")
    print(f"  autohiring voip call <号码>       # 拨打网络电话")
    print(f"  autohiring tts generate <文字>    # 文字转语音")

    if chromedriver_path:
        print(f"\nChromeDriver 路径: {chromedriver_path}")


if __name__ == "__main__":
    main()
