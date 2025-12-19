"""CLI主入口 - 动态加载命令"""

import importlib
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="招聘辅助CLI工具")
console = Console()


def load_commands():
    """动态加载commands目录下的所有命令"""
    commands_path = Path(__file__).parent / "commands"

    if not commands_path.exists():
        return

    for item in commands_path.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            try:
                module = importlib.import_module(f"autohiring.commands.{item.name}")
                if hasattr(module, "app"):
                    app.add_typer(module.app, name=item.name)
            except ImportError as e:
                console.print(f"[yellow]警告: 加载 {item.name} 失败: {e}[/yellow]")


# 加载所有命令
load_commands()


@app.command()
def version():
    """显示版本信息"""
    from autohiring import __version__
    console.print(f"autohiring v{__version__}")


@app.command()
def shell():
    """启动交互式命令行"""
    from rich.prompt import Prompt

    console.print("[bold green]AutoHiring 交互式命令行[/bold green]")
    console.print("输入命令（如: phone lookup 13800138000），输入 exit 退出\n")

    while True:
        try:
            cmd = Prompt.ask("[cyan]autohiring[/cyan]")
            if cmd.lower() in ("exit", "quit", "q"):
                console.print("[yellow]再见！[/yellow]")
                break
            if not cmd.strip():
                continue

            # 解析并执行命令
            args = cmd.split()
            try:
                app(args, standalone_mode=False)
            except SystemExit:
                pass
            except Exception as e:
                console.print(f"[red]错误: {e}[/red]")

        except KeyboardInterrupt:
            console.print("\n[yellow]再见！[/yellow]")
            break


if __name__ == "__main__":
    app()
