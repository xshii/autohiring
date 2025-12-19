"""电话号码归属地查询命令（离线查询）"""

import typer
import phonenumbers
from phonenumbers import geocoder
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="电话号码归属地查询（离线）")
console = Console()


@app.command("lookup")
def lookup(number: str):
    """查询单个电话号码归属地"""
    result = lookup_phone(number)
    console.print(result)


@app.command("batch")
def batch(file: str):
    """批量查询（从文件读取，每行一个号码）"""
    from pathlib import Path

    numbers = Path(file).read_text().strip().split("\n")
    results = batch_lookup(numbers)

    table = Table(title=f"批量查询结果（共{len(results)}条）")
    table.add_column("号码", style="cyan")
    table.add_column("归属地", style="green")

    for r in results:
        table.add_row(r["number"], r["location"] or "未知")

    console.print(table)


@app.command("csv")
def csv_batch(
    file: str = typer.Argument(..., help="CSV 文件路径"),
    column: str = typer.Option(..., "--col", "-c", help="电话号码列名"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径（默认覆盖原文件）"),
):
    """从 CSV 文件批量查询，结果追加到电话列后面"""
    import csv
    from pathlib import Path

    input_path = Path(file)
    output_path = Path(output) if output else input_path

    # 读取 CSV
    with open(input_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    if column not in fieldnames:
        console.print(f"[red]错误: 列 '{column}' 不存在[/red]")
        console.print(f"可用列: {', '.join(fieldnames)}")
        return

    # 添加归属地列
    col_index = fieldnames.index(column)
    if "归属地" not in fieldnames:
        fieldnames.insert(col_index + 1, "归属地")

    # 查询并填充
    console.print(f"[dim]处理 {len(rows)} 条记录...[/dim]")
    for row in rows:
        phone = row.get(column, "").strip()
        row["归属地"] = lookup_single(phone) if phone else ""

    # 写入 CSV
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    console.print(f"[green]✓ 已保存到 {output_path}[/green]")


def lookup_phone(number: str) -> Table:
    """查询电话号码归属地"""
    if not number.startswith("+"):
        number = "+86" + number.lstrip("0")

    try:
        parsed = phonenumbers.parse(number)
        location = geocoder.description_for_number(parsed, "zh")

        table = Table(title="电话号码信息")
        table.add_column("属性", style="cyan")
        table.add_column("值", style="green")

        table.add_row("号码", phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL))
        table.add_row("归属地", location or "未知")

        return table

    except phonenumbers.NumberParseException as e:
        table = Table(title="查询失败")
        table.add_column("错误", style="red")
        table.add_row(str(e))
        return table


def lookup_single(number: str) -> str:
    """查询单个电话号码归属地，返回字符串"""
    if not number.startswith("+"):
        number = "+86" + number.lstrip("0")

    try:
        parsed = phonenumbers.parse(number)
        return geocoder.description_for_number(parsed, "zh") or ""
    except phonenumbers.NumberParseException:
        return ""


def batch_lookup(numbers: list[str]) -> list[dict]:
    """批量查询电话号码归属地"""
    return [{"number": n, "location": lookup_single(n)} for n in numbers]
