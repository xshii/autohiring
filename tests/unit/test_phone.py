"""电话号码归属地查询单元测试"""

import pytest
from autohiring.commands.phone.command import lookup_single, batch_lookup


class TestLookupSingle:
    """测试单个号码查询"""

    def test_mobile_beijing(self):
        """北京手机号"""
        result = lookup_single("13800138000")
        assert "北京" in result

    def test_mobile_shanghai(self):
        """上海手机号"""
        result = lookup_single("13916888888")
        assert "上海" in result

    def test_mobile_with_prefix(self):
        """带 +86 前缀"""
        result = lookup_single("+8613800138000")
        assert "北京" in result

    def test_invalid_number(self):
        """无效号码返回空字符串"""
        result = lookup_single("123")
        assert result == ""

    def test_empty_string(self):
        """空字符串"""
        result = lookup_single("")
        assert result == ""


class TestBatchLookup:
    """测试批量查询"""

    def test_batch_multiple(self):
        """批量查询多个号码"""
        numbers = ["13800138000", "13912345678", "15088886666"]
        results = batch_lookup(numbers)

        assert len(results) == 3
        assert "北京" in results[0]["location"]
        assert "江苏" in results[1]["location"]
        assert "浙江" in results[2]["location"]

    def test_batch_empty_list(self):
        """空列表"""
        results = batch_lookup([])
        assert results == []

    def test_batch_with_invalid(self):
        """包含无效号码"""
        numbers = ["13800138000", "invalid", "13912345678"]
        results = batch_lookup(numbers)

        assert len(results) == 3
        assert "北京" in results[0]["location"]
        assert results[1]["location"] == ""
        assert "江苏" in results[2]["location"]


class TestEdgeCases:
    """边界情况测试"""

    def test_landline_number(self):
        """固定电话"""
        result = lookup_single("01012345678")
        assert result == "" or "北京" in result

    def test_number_with_leading_zero(self):
        """带前导零的号码"""
        result = lookup_single("013800138000")
        assert "北京" in result
