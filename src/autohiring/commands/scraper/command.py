"""网页自动化命令 - 使用 Selenium + YAML 配置"""

import csv
import json
import random
import re
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="网页自动化（Selenium + YAML）")
console = Console()

# 全局 driver
_driver = None
# 收集的数据
_collected_data = []


def get_driver(headless: bool = False):
    """获取 ChromeDriver"""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver_path = Path(__file__).parents[4] / "drivers" / "chromedriver"
    if driver_path.exists():
        service = Service(str(driver_path))
        return webdriver.Chrome(service=service, options=options)

    return webdriver.Chrome(options=options)


def parse_wait_time(value: str) -> float:
    """
    解析等待时间

    支持格式:
      "2"      → 固定 2 秒
      "3,60"   → 3 到 60 秒之间的随机时间
    """
    if not value:
        return 0

    value = str(value).strip()
    if "," in value:
        parts = value.split(",")
        min_sec = float(parts[0])
        max_sec = float(parts[1])
        return random.uniform(min_sec, max_sec)
    else:
        return float(value)


def load_csv(csv_path: str, config_dir: Path = None) -> List[Dict[str, str]]:
    """
    加载 CSV 文件，返回字典列表

    Args:
        csv_path: CSV 文件路径（可以是相对于配置文件的路径）
        config_dir: 配置文件所在目录
    """
    path = Path(csv_path)
    if not path.is_absolute() and config_dir:
        path = config_dir / csv_path

    if not path.exists():
        raise FileNotFoundError(f"CSV 文件不存在: {path}")

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))

    return rows


def substitute_variables(value: Any, variables: Dict[str, str]) -> Any:
    """
    替换字符串中的 ${col_name} 变量

    Args:
        value: 要替换的值（可以是字符串、字典或列表）
        variables: 变量字典 {col_name: value}
    """
    if isinstance(value, str):
        # 替换 ${col_name} 格式的变量
        def replace_var(match):
            var_name = match.group(1)
            return variables.get(var_name, match.group(0))

        return re.sub(r'\$\{([^}]+)\}', replace_var, value)

    elif isinstance(value, dict):
        return {k: substitute_variables(v, variables) for k, v in value.items()}

    elif isinstance(value, list):
        return [substitute_variables(item, variables) for item in value]

    return value


def build_xpath(rule: Dict[str, Any]) -> str:
    """
    从规则构建 XPath

    规则格式:
      tag: div
      class: card
      id: main
      text: 张三
      attr: {name: value}

    生成: //div[@class="card" and @id="main" and contains(text(), "张三")]
    """
    tag = rule.get("tag", "*")
    conditions = []

    if "class" in rule:
        conditions.append(f'@class="{rule["class"]}"')
    if "id" in rule:
        conditions.append(f'@id="{rule["id"]}"')
    if "text" in rule:
        conditions.append(f'contains(text(), "{rule["text"]}")')
    if "attr" in rule:
        for k, v in rule["attr"].items():
            conditions.append(f'@{k}="{v}"')

    if conditions:
        return f"//{tag}[{' and '.join(conditions)}]"
    return f"//{tag}"


def find_elements(xpath: str, context=None) -> list:
    """在上下文中查找元素"""
    from selenium.webdriver.common.by import By

    try:
        if context is not None:
            if xpath.startswith("//"):
                xpath = "." + xpath
            return context.find_elements(By.XPATH, xpath)
        return _driver.find_elements(By.XPATH, xpath)
    except Exception:
        return []


def execute_action(action: str, element=None, value: str = None, field: str = None):
    """
    执行动作

    Args:
        action: 动作类型 (click, input, enter, extract, save, print, wait, sleep)
        element: 目标元素
        value: 动作值（input 的文字、wait 的秒数等）
        field: 字段名（save 动作用于指定保存的字段名）
    """
    from selenium.webdriver.common.keys import Keys

    if action == "click":
        if element:
            _driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.2)
            element.click()
            console.print("[green]  ✓ 点击[/green]")

    elif action == "input":
        if element and value:
            element.clear()
            element.send_keys(value)
            console.print(f"[green]  ✓ 输入: {value}[/green]")

    elif action == "enter":
        if element:
            element.send_keys(Keys.RETURN)
        else:
            _driver.switch_to.active_element.send_keys(Keys.RETURN)
        console.print("[green]  ✓ 回车[/green]")

    elif action == "extract":
        if element:
            text = element.text
            console.print(f"[cyan]  文本: {text[:50]}...[/cyan]" if len(text) > 50 else f"[cyan]  文本: {text}[/cyan]")
            return {"text": text}

    elif action == "save":
        # 保存元素文本到指定字段，或保存 value 值
        field_name = field or "saved"
        if element:
            text = element.text
            console.print(f"[green]  ✓ 保存 {field_name}: {text[:30]}...[/green]" if len(text) > 30 else f"[green]  ✓ 保存 {field_name}: {text}[/green]")
            return {field_name: text}
        elif value:
            console.print(f"[green]  ✓ 保存 {field_name}: {value}[/green]")
            return {field_name: value}

    elif action == "print":
        # 打印元素文本或 value 值到控制台
        if element:
            text = element.text
            console.print(f"[yellow]  >>> {text}[/yellow]")
        elif value:
            console.print(f"[yellow]  >>> {value}[/yellow]")

    elif action == "wait":
        # 先等待页面加载完成
        wait_for_page_ready()
        # 再额外等待（支持随机: "3,60" 或 固定: "2"）
        seconds = parse_wait_time(value)
        if seconds > 0:
            time.sleep(seconds)
        console.print(f"[dim]  页面就绪 + {seconds:.1f}s[/dim]")

    elif action == "sleep":
        # 纯粹等待，不检查页面状态（支持随机）
        seconds = parse_wait_time(value) if value else 1
        time.sleep(seconds)
        console.print(f"[dim]  等待 {seconds:.1f}s[/dim]")

    return None


def wait_for_page_ready(timeout: int = 10):
    """等待页面加载完成"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    try:
        WebDriverWait(_driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except Exception:
        pass  # 超时就继续


def execute_step(step: Dict[str, Any], context=None) -> List[Any]:
    """
    执行单个步骤

    步骤格式:
      - tag: div
        class: card
        select: "*"      # * = 全部, 1 = 第一个, 2 = 第二个...
        action: click    # click, input, enter, extract, save, print, wait
        value: "xxx"     # input 的值、print 的内容
        field: "name"    # save 动作的字段名
        children:        # 子步骤
          - tag: span
            ...
    """
    xpath = build_xpath(step)
    select = step.get("select", 1)
    action = step.get("action")
    value = step.get("value")
    field = step.get("field")
    children = step.get("children", [])

    console.print(f"[cyan]查找: {xpath}[/cyan]")

    # 查找元素
    elements = find_elements(xpath, context)

    if not elements:
        console.print(f"[yellow]  未找到元素[/yellow]")
        return []

    console.print(f"[green]  找到 {len(elements)} 个[/green]")

    # 选择元素
    if select == "*":
        selected = elements
    elif isinstance(select, int):
        if 1 <= select <= len(elements):
            selected = [elements[select - 1]]
        else:
            console.print(f"[red]  无效索引: {select}[/red]")
            return []
    else:
        selected = elements

    results = []

    # 对每个选中元素执行动作和子步骤
    for i, el in enumerate(selected, 1):
        if len(selected) > 1:
            console.print(f"[dim]  --- 元素 {i}/{len(selected)} ---[/dim]")

        # 执行动作
        if action:
            result = execute_action(action, el, value, field)
            if result:
                results.append(result)
            time.sleep(0.3)

        # 执行子步骤
        for child in children:
            child_results = execute_step(child, el)
            results.extend(child_results)

    return results


def load_config(config_path: str) -> Dict[str, Any]:
    """加载 YAML 配置"""
    import yaml

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@app.command("run")
def run(
    config: str = typer.Argument(..., help="YAML 配置文件路径"),
    output: str = typer.Option("data.json", "-o", "--output", help="输出文件"),
):
    """根据 YAML 配置执行自动化流程"""
    global _driver, _collected_data

    try:
        import yaml
    except ImportError:
        console.print("[red]请安装 PyYAML: pip install pyyaml[/red]")
        return

    # 加载配置
    try:
        cfg = load_config(config)
    except Exception as e:
        console.print(f"[red]加载配置失败: {e}[/red]")
        return

    url = cfg.get("url")
    steps = cfg.get("steps", [])
    wait_login = cfg.get("wait_login", False)
    csv_file = cfg.get("csv")

    if not url:
        console.print("[red]配置缺少 url[/red]")
        return

    # 加载 CSV 数据（如果配置了）
    config_dir = Path(config).parent
    csv_rows = []
    if csv_file:
        try:
            csv_rows = load_csv(csv_file, config_dir)
            console.print(f"[cyan]已加载 CSV: {csv_file} ({len(csv_rows)} 行)[/cyan]")
        except Exception as e:
            console.print(f"[red]加载 CSV 失败: {e}[/red]")
            return

    console.print(f"[bold]执行配置: {config}[/bold]")
    console.print(f"URL: {url}")
    console.print(f"步骤数: {len(steps)}")
    if csv_rows:
        console.print(f"CSV 循环: {len(csv_rows)} 次\n")
    else:
        console.print()

    # 启动浏览器
    _driver = get_driver()
    _driver.get(url)
    _collected_data = []

    console.print(f"[green]已打开: {url}[/green]")

    # 等待登录
    if wait_login:
        console.print("[yellow]请登录后按 Enter 继续...[/yellow]")
        input()

    try:
        if csv_rows:
            # CSV 循环模式：对每一行执行所有步骤
            for row_idx, row in enumerate(csv_rows, 1):
                console.print(f"\n[bold magenta]===== CSV 行 {row_idx}/{len(csv_rows)} =====[/bold magenta]")
                console.print(f"[dim]{row}[/dim]")

                # 替换步骤中的变量
                substituted_steps = substitute_variables(steps, row)

                # 执行步骤
                for i, step in enumerate(substituted_steps, 1):
                    console.print(f"\n[bold]步骤 {i}/{len(substituted_steps)}[/bold]")
                    results = execute_step(step)
                    # 给结果添加 CSV 行信息
                    for r in results:
                        r["_csv_row"] = row_idx
                        r.update(row)
                    _collected_data.extend(results)
        else:
            # 普通模式：执行一次所有步骤
            for i, step in enumerate(steps, 1):
                console.print(f"\n[bold]步骤 {i}/{len(steps)}[/bold]")
                results = execute_step(step)
                _collected_data.extend(results)

        # 保存数据
        if _collected_data:
            Path(output).write_text(
                json.dumps(_collected_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            console.print(f"\n[green]✓ 已保存 {len(_collected_data)} 条数据到 {output}[/green]")

        console.print("\n[bold green]执行完成[/bold green]")

    except Exception as e:
        console.print(f"[red]执行失败: {e}[/red]")

    finally:
        console.print("[yellow]按 Enter 关闭浏览器...[/yellow]")
        input()
        if _driver:
            _driver.quit()


@app.command("interactive")
def interactive(
    url: str = typer.Argument(..., help="起始 URL"),
):
    """交互模式 - 手动探索页面"""
    global _driver

    console.print("[bold]启动浏览器...[/bold]")
    _driver = get_driver()
    _driver.get(url)

    console.print(f"[green]已打开: {url}[/green]")
    console.print("\n[bold]命令：[/bold]")
    console.print("  find <xpath>    查找元素")
    console.print("  click <n>       点击第n个")
    console.print("  input <text>    输入文字")
    console.print("  wait <s>        等待")
    console.print("  quit            退出\n")

    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys

    current_elements = []

    while True:
        try:
            cmd = input("> ").strip()
            if not cmd:
                continue

            if cmd.lower() in ("quit", "q"):
                break

            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if action == "find":
                xpath = arg if arg.startswith("//") else f"//*[contains(text(), '{arg}')]"
                current_elements = _driver.find_elements(By.XPATH, xpath)
                console.print(f"找到 {len(current_elements)} 个")
                for i, el in enumerate(current_elements[:10], 1):
                    text = el.text[:30].replace("\n", " ")
                    console.print(f"  {i}. {el.tag_name}: {text}")

            elif action == "click":
                n = int(arg) if arg else 1
                if 1 <= n <= len(current_elements):
                    current_elements[n-1].click()
                    console.print("✓ 已点击")
                    time.sleep(0.5)

            elif action == "input":
                _driver.switch_to.active_element.send_keys(arg)
                console.print(f"✓ 已输入: {arg}")

            elif action == "enter":
                _driver.switch_to.active_element.send_keys(Keys.RETURN)
                console.print("✓ 回车")

            elif action == "wait":
                time.sleep(float(arg) if arg else 1)

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")

    if _driver:
        _driver.quit()


@app.command("example")
def example():
    """显示 YAML 配置示例"""
    example_yaml = '''# 示例配置文件
url: "https://example.com"
wait_login: true  # 等待手动登录

# CSV 循环（可选）：从 CSV 读取数据，对每行执行 steps
# csv: "data.csv"
# CSV 文件格式：
#   工号,姓名
#   12345,张三
#   67890,李四

steps:
  # 步骤1: 在搜索框输入（使用 ${col_name} 引用 CSV 列）
  - tag: input
    attr:
      placeholder: "搜索"
    action: input
    value: "${工号}"     # 会被替换为 CSV 中的工号值

  # 步骤2: 点击搜索按钮
  - tag: button
    text: "搜索"
    action: click

  # 步骤3: 等待结果（支持随机时间）
  - action: wait
    value: "3,10"        # 3 到 10 秒之间随机

  # 步骤4: 打印当前搜索的工号
  - action: print
    value: "正在处理: ${工号}"

  # 步骤5: 遍历所有卡片
  - tag: div
    class: "card"
    select: "*"           # * 表示全部
    children:
      # 对每个卡片，点击详情
      - tag: a
        text: "详情"
        action: click

      # 等待页面加载
      - action: wait
        value: "1"

      # 保存姓名到指定字段
      - tag: span
        class: "name"
        action: save
        field: "候选人姓名"    # 保存到 "候选人姓名" 字段

      # 保存电话
      - tag: span
        class: "phone"
        action: save
        field: "电话"

      # 打印提取的内容
      - tag: span
        class: "status"
        action: print         # 打印到控制台（不保存）

      # 返回
      - tag: a
        text: "返回"
        action: click
'''
    console.print(example_yaml)
    console.print("\n[dim]保存为 config.yaml 后运行: autohiring scraper run config.yaml[/dim]")
    console.print("[dim]CSV 循环: 取消 csv 行注释，运行时会为每行数据执行一遍 steps[/dim]")
