"""TTS语音合成命令"""

import asyncio

import typer
from rich.console import Console

app = typer.Typer(help="TTS语音合成")
console = Console()

# 常用话术模板
TEMPLATES = {
    "initial_contact": """
您好，这里是{company}的招聘团队。
我们在{platform}上看到了您的简历，觉得您的背景很符合我们{position}岗位的要求。
请问您现在方便简单聊几句吗？
""",
    "intention_survey": """
您好，我是{company}的HR{name}。
想跟您确认一下，您目前是否有换工作的意向呢？
如果有的话，请按1；暂时不考虑请按2。
""",
    "interview_invite": """
您好，恭喜您通过了{company}{position}岗位的简历筛选。
我们想邀请您参加面试，时间初定在{time}。
如果方便请按1确认，需要改期请按2。
""",
}


@app.command("generate")
def generate(
    text: str = typer.Argument(..., help="要转换的文字"),
    output: str = typer.Option("output.mp3", help="输出文件路径"),
    voice: str = typer.Option("zh-CN-XiaoxiaoNeural", help="语音类型"),
):
    """文字转语音"""
    asyncio.run(_generate_speech(text, output, voice))


@app.command("template")
def template(
    name: str = typer.Argument(..., help="模板名称"),
    output: str = typer.Option("output.mp3", help="输出文件路径"),
    voice: str = typer.Option("zh-CN-XiaoxiaoNeural", help="语音类型"),
    company: str = typer.Option("", help="公司名"),
    position: str = typer.Option("", help="职位名"),
    platform: str = typer.Option("", help="平台名"),
    hr_name: str = typer.Option("", "--name", help="HR姓名"),
    time: str = typer.Option("", help="面试时间"),
):
    """使用模板生成语音"""
    if name not in TEMPLATES:
        console.print(f"[red]未知模板: {name}[/red]")
        console.print(f"可用模板: {', '.join(TEMPLATES.keys())}")
        return

    text = TEMPLATES[name].format(
        company=company,
        position=position,
        platform=platform,
        name=hr_name,
        time=time,
    ).strip()

    console.print(f"[dim]生成内容: {text}[/dim]")
    asyncio.run(_generate_speech(text, output, voice))


@app.command("voices")
def voices():
    """列出可用的中文语音"""
    asyncio.run(_list_voices())


@app.command("templates")
def list_templates():
    """列出可用的话术模板"""
    from rich.table import Table

    table = Table(title="可用话术模板")
    table.add_column("名称", style="cyan")
    table.add_column("说明", style="green")

    table.add_row("initial_contact", "初次联系候选人")
    table.add_row("intention_survey", "意向调查")
    table.add_row("interview_invite", "面试邀请")

    console.print(table)


async def _generate_speech(text: str, output: str, voice: str):
    """使用edge-tts生成语音"""
    try:
        import edge_tts

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output)
        console.print(f"[green]✓ 语音已生成: {output}[/green]")

    except ImportError:
        console.print("[red]错误: 请安装edge-tts[/red]")
        console.print("pip install edge-tts")


async def _list_voices():
    """列出可用的语音"""
    try:
        import edge_tts

        voices = await edge_tts.list_voices()
        zh_voices = [v for v in voices if v["Locale"].startswith("zh")]

        from rich.table import Table

        table = Table(title="可用的中文语音")
        table.add_column("名称", style="cyan")
        table.add_column("性别", style="green")
        table.add_column("地区", style="yellow")

        for v in zh_voices:
            table.add_row(v["ShortName"], v["Gender"], v["Locale"])

        console.print(table)

    except ImportError:
        console.print("[red]错误: 请安装edge-tts[/red]")
        console.print("pip install edge-tts")
