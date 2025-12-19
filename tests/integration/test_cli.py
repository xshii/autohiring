"""CLI 测试"""

import pytest
from typer.testing import CliRunner

from autohiring.cli import app


runner = CliRunner()


class TestCli:
    """测试 CLI 主入口"""

    def test_help(self):
        """测试帮助信息"""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "招聘辅助CLI工具" in result.stdout

    def test_version(self):
        """测试版本命令"""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "autohiring v" in result.stdout

    def test_phone_help(self):
        """测试 phone 子命令帮助"""
        result = runner.invoke(app, ["phone", "--help"])
        assert result.exit_code == 0
        assert "归属地" in result.stdout

    def test_phone_lookup(self):
        """测试电话查询"""
        result = runner.invoke(app, ["phone", "lookup", "13800138000"])
        assert result.exit_code == 0
        assert "北京" in result.stdout

    def test_scraper_help(self):
        """测试 scraper 子命令帮助"""
        result = runner.invoke(app, ["scraper", "--help"])
        assert result.exit_code == 0

    def test_voip_config(self):
        """测试 voip 配置显示"""
        result = runner.invoke(app, ["voip", "config"])
        assert result.exit_code == 0
        assert "阿里云" in result.stdout

    def test_tts_help(self):
        """测试 tts 子命令帮助"""
        result = runner.invoke(app, ["tts", "--help"])
        assert result.exit_code == 0
