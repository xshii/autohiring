"""网页自动化单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from autohiring.commands.scraper.command import (
    build_xpath,
    parse_wait_time,
    load_csv,
    substitute_variables,
    _collected_data,
)


class TestParseWaitTime:
    """测试等待时间解析"""

    def test_fixed_time(self):
        """固定时间"""
        assert parse_wait_time("2") == 2.0
        assert parse_wait_time("0.5") == 0.5

    def test_random_time(self):
        """随机时间"""
        result = parse_wait_time("3,60")
        assert 3 <= result <= 60

    def test_random_time_multiple_calls(self):
        """随机时间多次调用应产生不同值"""
        results = [parse_wait_time("1,100") for _ in range(10)]
        # 10次调用不应该全部相同
        assert len(set(results)) > 1

    def test_empty_value(self):
        """空值返回0"""
        assert parse_wait_time("") == 0
        assert parse_wait_time(None) == 0

    def test_string_number(self):
        """字符串数字"""
        assert parse_wait_time("10") == 10.0


class TestSubstituteVariables:
    """测试变量替换"""

    def test_simple_string(self):
        """简单字符串替换"""
        result = substitute_variables("Hello ${name}", {"name": "张三"})
        assert result == "Hello 张三"

    def test_multiple_variables(self):
        """多个变量"""
        result = substitute_variables("${工号}: ${姓名}", {"工号": "12345", "姓名": "李四"})
        assert result == "12345: 李四"

    def test_missing_variable(self):
        """缺失变量保持原样"""
        result = substitute_variables("${missing}", {"name": "test"})
        assert result == "${missing}"

    def test_dict_substitution(self):
        """字典中的替换"""
        data = {"value": "${工号}", "tag": "input"}
        result = substitute_variables(data, {"工号": "99999"})
        assert result["value"] == "99999"
        assert result["tag"] == "input"

    def test_list_substitution(self):
        """列表中的替换"""
        data = ["${a}", "${b}", "固定"]
        result = substitute_variables(data, {"a": "1", "b": "2"})
        assert result == ["1", "2", "固定"]

    def test_nested_substitution(self):
        """嵌套结构替换"""
        data = {
            "step": {
                "value": "${工号}",
                "children": [{"text": "${姓名}"}]
            }
        }
        result = substitute_variables(data, {"工号": "123", "姓名": "王五"})
        assert result["step"]["value"] == "123"
        assert result["step"]["children"][0]["text"] == "王五"

    def test_non_string_passthrough(self):
        """非字符串值直接返回"""
        assert substitute_variables(123, {"x": "y"}) == 123
        assert substitute_variables(None, {"x": "y"}) is None


class TestLoadCsv:
    """测试 CSV 加载"""

    def test_load_csv(self, tmp_path):
        """加载 CSV 文件"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("工号,姓名\n12345,张三\n67890,李四", encoding="utf-8")

        rows = load_csv(str(csv_file))
        assert len(rows) == 2
        assert rows[0]["工号"] == "12345"
        assert rows[0]["姓名"] == "张三"
        assert rows[1]["工号"] == "67890"

    def test_load_csv_relative_path(self, tmp_path):
        """相对路径加载"""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("id,name\n1,test", encoding="utf-8")

        rows = load_csv("data.csv", tmp_path)
        assert len(rows) == 1
        assert rows[0]["id"] == "1"

    def test_load_csv_not_found(self):
        """文件不存在"""
        with pytest.raises(FileNotFoundError):
            load_csv("/nonexistent/file.csv")

    def test_load_csv_empty(self, tmp_path):
        """空 CSV（只有表头）"""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("col1,col2\n", encoding="utf-8")

        rows = load_csv(str(csv_file))
        assert rows == []


class TestBuildXpath:
    """测试 XPath 构建"""

    def test_tag_only(self):
        """只有标签"""
        result = build_xpath({"tag": "div"})
        assert result == "//div"

    def test_with_class(self):
        """带 class"""
        result = build_xpath({"tag": "div", "class": "card"})
        assert result == '//div[@class="card"]'

    def test_with_id(self):
        """带 id"""
        result = build_xpath({"tag": "span", "id": "main"})
        assert result == '//span[@id="main"]'

    def test_with_text(self):
        """带文本"""
        result = build_xpath({"tag": "button", "text": "提交"})
        assert result == '//button[contains(text(), "提交")]'

    def test_with_attr(self):
        """带自定义属性"""
        result = build_xpath({"tag": "input", "attr": {"placeholder": "搜索"}})
        assert result == '//input[@placeholder="搜索"]'

    def test_multiple_conditions(self):
        """多个条件"""
        result = build_xpath({"tag": "div", "class": "card", "id": "main"})
        assert '@class="card"' in result
        assert '@id="main"' in result
        assert " and " in result

    def test_wildcard_tag(self):
        """通配符标签"""
        result = build_xpath({"text": "点击"})
        assert result == '//*[contains(text(), "点击")]'


class TestCollectedData:
    """测试数据收集"""

    def setup_method(self):
        _collected_data.clear()

    def test_append_data(self):
        _collected_data.append({"text": "张三"})
        assert len(_collected_data) == 1

    def test_clear_data(self):
        _collected_data.append({"text": "测试"})
        _collected_data.clear()
        assert len(_collected_data) == 0


class TestFindElements:
    """测试元素查找"""

    @patch("autohiring.commands.scraper.command._driver")
    def test_find_without_context(self, mock_driver):
        from autohiring.commands.scraper.command import find_elements

        mock_driver.find_elements.return_value = [Mock()]
        result = find_elements("//div")

        mock_driver.find_elements.assert_called_once()
        assert len(result) == 1

    @patch("autohiring.commands.scraper.command._driver")
    def test_find_with_context(self, mock_driver):
        from autohiring.commands.scraper.command import find_elements

        context = Mock()
        context.find_elements.return_value = [Mock(), Mock()]

        result = find_elements("//span", context)

        context.find_elements.assert_called_once()
        assert len(result) == 2


class TestExecuteAction:
    """测试动作执行"""

    @patch("autohiring.commands.scraper.command._driver")
    def test_click_action(self, mock_driver):
        from autohiring.commands.scraper.command import execute_action

        element = Mock()
        execute_action("click", element)

        element.click.assert_called_once()

    @patch("autohiring.commands.scraper.command._driver")
    def test_input_action(self, mock_driver):
        from autohiring.commands.scraper.command import execute_action

        element = Mock()
        execute_action("input", element, "测试文字")

        element.clear.assert_called_once()
        element.send_keys.assert_called_once_with("测试文字")

    def test_extract_action(self):
        from autohiring.commands.scraper.command import execute_action

        element = Mock()
        element.text = "提取的文本"

        result = execute_action("extract", element)

        assert result == {"text": "提取的文本"}

    def test_save_action_with_element(self):
        from autohiring.commands.scraper.command import execute_action

        element = Mock()
        element.text = "保存的内容"

        result = execute_action("save", element, field="姓名")

        assert result == {"姓名": "保存的内容"}

    def test_save_action_with_value(self):
        from autohiring.commands.scraper.command import execute_action

        result = execute_action("save", value="直接值", field="工号")

        assert result == {"工号": "直接值"}

    def test_save_action_default_field(self):
        from autohiring.commands.scraper.command import execute_action

        element = Mock()
        element.text = "默认字段"

        result = execute_action("save", element)

        assert result == {"saved": "默认字段"}

    def test_print_action(self):
        from autohiring.commands.scraper.command import execute_action

        element = Mock()
        element.text = "打印内容"

        # print 不返回值
        result = execute_action("print", element)
        assert result is None

    def test_print_action_with_value(self):
        from autohiring.commands.scraper.command import execute_action

        result = execute_action("print", value="直接打印")
        assert result is None


class TestGetDriver:
    """测试 ChromeDriver 获取"""

    @patch("selenium.webdriver.Chrome")
    @patch("selenium.webdriver.chrome.service.Service")
    @patch("selenium.webdriver.chrome.options.Options")
    def test_get_driver(self, mock_options, mock_service, mock_chrome):
        from autohiring.commands.scraper.command import get_driver

        with patch.object(Path, "exists", return_value=False):
            driver = get_driver()
            mock_chrome.assert_called_once()
