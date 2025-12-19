"""反爬虫检测模块单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from autohiring.commands.scraper.ua_pool import (
    get_random_ua,
    get_random_resolution,
    get_random_language,
    get_random_timezone,
    get_random_webgl_info,
    UARotator,
    CHROME_UA_POOL,
    EDGE_UA_POOL,
    FIREFOX_UA_POOL,
    MIXED_UA_POOL,
    SCREEN_RESOLUTIONS,
    LANGUAGES,
    TIMEZONES,
    WEBGL_VENDORS,
)
from autohiring.commands.scraper.anti_detect import (
    AntiDetect,
    STEALTH_JS,
    CANVAS_FINGERPRINT_JS,
    get_webgl_spoof_js,
    AUDIO_FINGERPRINT_JS,
)


class TestGetRandomUA:
    """测试随机 User-Agent 获取"""

    def test_chrome_ua(self):
        """Chrome UA"""
        ua = get_random_ua("chrome")
        assert ua in CHROME_UA_POOL
        assert "Chrome" in ua

    def test_edge_ua(self):
        """Edge UA"""
        ua = get_random_ua("edge")
        assert ua in EDGE_UA_POOL
        assert "Edg" in ua

    def test_firefox_ua(self):
        """Firefox UA"""
        ua = get_random_ua("firefox")
        assert ua in FIREFOX_UA_POOL
        assert "Firefox" in ua

    def test_mixed_ua(self):
        """混合 UA"""
        ua = get_random_ua()
        assert ua in MIXED_UA_POOL

    def test_random_different_values(self):
        """随机调用产生不同值"""
        results = [get_random_ua() for _ in range(20)]
        # 20次调用应该有多个不同值
        assert len(set(results)) > 1


class TestGetRandomResolution:
    """测试随机分辨率获取"""

    def test_valid_resolution(self):
        """有效分辨率"""
        width, height = get_random_resolution()
        assert (width, height) in SCREEN_RESOLUTIONS
        assert width > 0
        assert height > 0

    def test_random_different_values(self):
        """随机调用产生不同值"""
        results = [get_random_resolution() for _ in range(20)]
        assert len(set(results)) > 1


class TestGetRandomLanguage:
    """测试随机语言获取"""

    def test_valid_language(self):
        """有效语言"""
        languages = get_random_language()
        assert languages in LANGUAGES
        assert len(languages) > 0

    def test_random_different_values(self):
        """随机调用产生不同值"""
        results = [tuple(get_random_language()) for _ in range(20)]
        assert len(set(results)) > 1


class TestGetRandomTimezone:
    """测试随机时区获取"""

    def test_valid_timezone(self):
        """有效时区"""
        tz = get_random_timezone()
        assert tz in TIMEZONES


class TestGetRandomWebglInfo:
    """测试随机 WebGL 信息获取"""

    def test_valid_webgl_info(self):
        """有效 WebGL 信息"""
        vendor, renderer = get_random_webgl_info()
        assert (vendor, renderer) in WEBGL_VENDORS
        assert len(vendor) > 0
        assert len(renderer) > 0


class TestUARotator:
    """测试 UA 轮换器"""

    def test_chrome_rotator(self):
        """Chrome 轮换器"""
        rotator = UARotator("chrome", shuffle=False)
        assert len(rotator) == len(CHROME_UA_POOL)

    def test_edge_rotator(self):
        """Edge 轮换器"""
        rotator = UARotator("edge", shuffle=False)
        assert len(rotator) == len(EDGE_UA_POOL)

    def test_mixed_rotator(self):
        """混合轮换器"""
        rotator = UARotator(shuffle=False)
        assert len(rotator) == len(MIXED_UA_POOL)

    def test_next_cycles(self):
        """轮换循环"""
        rotator = UARotator("chrome", shuffle=False)
        first_ua = rotator.next()

        # 循环一遍
        for _ in range(len(rotator) - 1):
            rotator.next()

        # 应该回到第一个
        assert rotator.next() == first_ua

    def test_reset(self):
        """重置"""
        rotator = UARotator("chrome", shuffle=False)
        first_ua = rotator.next()
        rotator.next()
        rotator.next()

        rotator.reset()
        assert rotator.next() == first_ua

    def test_shuffle(self):
        """打乱顺序"""
        # 多次创建打乱的轮换器，顺序应该不同
        orders = []
        for _ in range(5):
            rotator = UARotator("chrome", shuffle=True)
            order = [rotator.next() for _ in range(3)]
            orders.append(tuple(order))

        # 5次应该有不同的顺序
        assert len(set(orders)) > 1


class TestAntiDetect:
    """测试反爬虫检测类"""

    def test_default_config(self):
        """默认配置"""
        ad = AntiDetect()
        assert ad.stealth is True
        assert ad.random_ua is True
        assert ad.random_window is True
        assert ad.canvas_protect is True
        assert ad.webgl_spoof is True
        assert ad.audio_protect is False
        assert ad.human_delay is True
        assert ad.proxy is None

    def test_custom_config(self):
        """自定义配置"""
        config = {
            "stealth": False,
            "random_ua": False,
            "proxy": "http://127.0.0.1:8080"
        }
        ad = AntiDetect(config)
        assert ad.stealth is False
        assert ad.random_ua is False
        assert ad.proxy == "http://127.0.0.1:8080"
        # 默认值不变
        assert ad.random_window is True

    def test_apply_to_options_chrome(self):
        """应用到 Chrome 选项"""
        options = Mock()
        options.add_argument = Mock()
        options.add_experimental_option = Mock()

        ad = AntiDetect({"proxy": "http://proxy.test:8080"})
        ad.apply_to_options(options, "chrome")

        # 检查基础参数被添加
        args = [call[0][0] for call in options.add_argument.call_args_list]
        assert "--disable-blink-features=AutomationControlled" in args
        assert "--no-sandbox" in args
        assert "--disable-dev-shm-usage" in args
        assert any("--proxy-server=" in arg for arg in args)

    def test_apply_to_options_edge(self):
        """应用到 Edge 选项"""
        options = Mock()
        options.add_argument = Mock()
        options.add_experimental_option = Mock()

        ad = AntiDetect()
        ad.apply_to_options(options, "edge")

        args = [call[0][0] for call in options.add_argument.call_args_list]
        assert "--disable-blink-features=AutomationControlled" in args

    def test_inject_stealth_scripts(self):
        """注入隐身脚本"""
        driver = Mock()
        driver.execute_cdp_cmd = Mock()

        ad = AntiDetect({
            "stealth": True,
            "canvas_protect": True,
            "webgl_spoof": True,
            "audio_protect": False
        })
        ad.inject_stealth_scripts(driver)

        # 应该调用 CDP 命令
        driver.execute_cdp_cmd.assert_called_once()
        call_args = driver.execute_cdp_cmd.call_args
        assert call_args[0][0] == "Page.addScriptToEvaluateOnNewDocument"

    def test_randomize_window(self):
        """随机化窗口"""
        driver = Mock()
        driver.set_window_size = Mock()
        driver.set_window_position = Mock()

        ad = AntiDetect({"random_window": True})
        ad.randomize_window(driver)

        driver.set_window_size.assert_called_once()
        args = driver.set_window_size.call_args[0]
        assert args[0] > 0  # width
        assert args[1] > 0  # height

    def test_randomize_window_disabled(self):
        """禁用随机化窗口"""
        driver = Mock()

        ad = AntiDetect({"random_window": False})
        ad.randomize_window(driver)

        driver.set_window_size.assert_not_called()

    def test_human_like_delay(self):
        """人类行为延迟"""
        import time

        ad = AntiDetect({"human_delay": True})

        start = time.time()
        ad.human_like_delay(0.1, 0.2)
        elapsed = time.time() - start

        assert elapsed >= 0.1
        assert elapsed <= 0.5  # 给一些余量

    def test_human_like_delay_disabled(self):
        """禁用人类行为延迟"""
        import time

        ad = AntiDetect({"human_delay": False})

        start = time.time()
        ad.human_like_delay(1.0, 2.0)
        elapsed = time.time() - start

        assert elapsed < 0.1  # 应该立即返回

    def test_human_like_typing(self):
        """人类打字模拟"""
        element = Mock()

        ad = AntiDetect({"human_delay": True})
        ad.human_like_typing(element, "AB", min_delay=0.01, max_delay=0.02)

        # 应该逐字符输入
        assert element.send_keys.call_count == 2

    def test_human_like_typing_disabled(self):
        """禁用人类打字模拟"""
        element = Mock()

        ad = AntiDetect({"human_delay": False})
        ad.human_like_typing(element, "test")

        # 应该一次性输入
        element.send_keys.assert_called_once_with("test")

    def test_random_scroll(self):
        """随机滚动"""
        driver = Mock()
        driver.execute_script = Mock()

        ad = AntiDetect({"human_delay": True})
        ad.random_scroll(driver, times=2)

        # 应该调用两次滚动
        assert driver.execute_script.call_count == 2

    def test_random_mouse_movement(self):
        """随机鼠标移动"""
        driver = Mock()
        driver.execute_script = Mock()

        ad = AntiDetect()
        ad.random_mouse_movement(driver)

        # 应该调用多次鼠标移动
        assert driver.execute_script.call_count >= 2


class TestStealthScripts:
    """测试隐身脚本"""

    def test_stealth_js_content(self):
        """隐身脚本内容"""
        assert "navigator.webdriver" in STEALTH_JS
        assert "navigator.plugins" in STEALTH_JS
        assert "navigator.languages" in STEALTH_JS
        assert "chrome.runtime" in STEALTH_JS

    def test_canvas_fingerprint_js_content(self):
        """Canvas 指纹脚本内容"""
        assert "toDataURL" in CANVAS_FINGERPRINT_JS
        assert "getImageData" in CANVAS_FINGERPRINT_JS

    def test_webgl_spoof_js_generation(self):
        """WebGL 伪装脚本生成"""
        js = get_webgl_spoof_js("Test Vendor", "Test Renderer")
        assert "Test Vendor" in js
        assert "Test Renderer" in js
        assert "37445" in js  # UNMASKED_VENDOR_WEBGL
        assert "37446" in js  # UNMASKED_RENDERER_WEBGL

    def test_audio_fingerprint_js_content(self):
        """音频指纹脚本内容"""
        assert "AudioContext" in AUDIO_FINGERPRINT_JS
        assert "createOscillator" in AUDIO_FINGERPRINT_JS


class TestAntiDetectIntegration:
    """反爬虫检测集成测试"""

    def test_full_config_workflow(self):
        """完整配置工作流"""
        config = {
            "stealth": True,
            "random_ua": True,
            "random_window": True,
            "canvas_protect": True,
            "webgl_spoof": True,
            "audio_protect": True,
            "human_delay": True,
            "proxy": "http://proxy.test:8080"
        }

        ad = AntiDetect(config)

        # 验证所有配置正确加载
        assert ad.stealth is True
        assert ad.random_ua is True
        assert ad.random_window is True
        assert ad.canvas_protect is True
        assert ad.webgl_spoof is True
        assert ad.audio_protect is True
        assert ad.human_delay is True
        assert ad.proxy == "http://proxy.test:8080"

    def test_minimal_config_workflow(self):
        """最小配置工作流"""
        config = {
            "stealth": False,
            "random_ua": False,
            "random_window": False,
            "human_delay": False
        }

        ad = AntiDetect(config)

        assert ad.stealth is False
        assert ad.random_ua is False
        assert ad.random_window is False
        assert ad.human_delay is False
        # 未指定的使用默认值
        assert ad.canvas_protect is True
