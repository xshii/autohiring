"""网络电话命令 - 阿里云语音服务"""

import os
import time

import typer
from rich.console import Console

app = typer.Typer(help="网络电话（阿里云语音）")
console = Console()

# 阿里云配置（从环境变量读取）
ALIYUN_ACCESS_KEY_ID = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
ALIYUN_ACCESS_KEY_SECRET = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
ALIYUN_VOICE_SHOW_NUMBER = os.getenv("ALIYUN_VOICE_SHOW_NUMBER", "")
ALIYUN_VOICE_TTS_CODE = os.getenv("ALIYUN_VOICE_TTS_CODE", "")


def _check_config() -> bool:
    """检查阿里云配置"""
    if not all([ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET]):
        console.print("[red]错误: 请设置阿里云环境变量[/red]")
        console.print("  ALIYUN_ACCESS_KEY_ID")
        console.print("  ALIYUN_ACCESS_KEY_SECRET")
        console.print("  ALIYUN_VOICE_SHOW_NUMBER")
        console.print("  ALIYUN_VOICE_TTS_CODE")
        return False
    return True


@app.command("call")
def call(
    number: str = typer.Argument(..., help="被叫号码"),
    template: str = typer.Option(None, help="语音模板编码"),
):
    """拨打单个电话"""
    if not _check_config():
        return

    make_call(number, template)


@app.command("batch")
def batch(
    file: str = typer.Argument(..., help="号码文件（每行一个）"),
    template: str = typer.Option(None, help="语音模板编码"),
    interval: int = typer.Option(5, help="呼叫间隔（秒）"),
):
    """批量拨打电话"""
    if not _check_config():
        return

    from pathlib import Path

    numbers = Path(file).read_text().strip().split("\n")
    console.print(f"[bold]开始批量呼叫，共 {len(numbers)} 个号码[/bold]")

    for i, number in enumerate(numbers, 1):
        console.print(f"\n[{i}/{len(numbers)}] 呼叫 {number}")
        make_call(number.strip(), template)

        if i < len(numbers):
            console.print(f"[dim]等待 {interval} 秒后继续...[/dim]")
            time.sleep(interval)

    console.print("\n[bold green]批量呼叫完成[/bold green]")


@app.command("config")
def config():
    """显示当前配置"""
    table_data = [
        ("ALIYUN_ACCESS_KEY_ID", "***" if ALIYUN_ACCESS_KEY_ID else "[未设置]"),
        ("ALIYUN_ACCESS_KEY_SECRET", "***" if ALIYUN_ACCESS_KEY_SECRET else "[未设置]"),
        ("ALIYUN_VOICE_SHOW_NUMBER", ALIYUN_VOICE_SHOW_NUMBER or "[未设置]"),
        ("ALIYUN_VOICE_TTS_CODE", ALIYUN_VOICE_TTS_CODE or "[未设置]"),
    ]

    from rich.table import Table

    table = Table(title="阿里云语音配置")
    table.add_column("环境变量", style="cyan")
    table.add_column("值", style="green")

    for key, value in table_data:
        table.add_row(key, value)

    console.print(table)


def make_call(phone_number: str, template: str = None):
    """拨打网络电话"""
    try:
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkdyvmsapi.request.v20170525.SingleCallByTtsRequest import SingleCallByTtsRequest

        client = AcsClient(
            ALIYUN_ACCESS_KEY_ID,
            ALIYUN_ACCESS_KEY_SECRET,
            "cn-hangzhou"
        )

        request = SingleCallByTtsRequest()
        request.set_accept_format("json")
        request.set_CalledNumber(phone_number)
        request.set_CalledShowNumber(ALIYUN_VOICE_SHOW_NUMBER)
        request.set_TtsCode(template or ALIYUN_VOICE_TTS_CODE)

        response = client.do_action_with_exception(request)
        console.print(f"[green]✓ 呼叫已发起[/green]: {phone_number}")
        console.print(f"[dim]响应: {response.decode('utf-8')}[/dim]")

    except ImportError:
        console.print("[red]错误: 请安装阿里云SDK[/red]")
        console.print("pip install aliyun-python-sdk-core aliyun-python-sdk-dyvmsapi")
    except Exception as e:
        console.print(f"[red]呼叫失败: {e}[/red]")
