"""User-Agent 池 - 提供多种浏览器 UA 用于轮换"""

import random
from typing import Optional

# Chrome User-Agent 池 (Windows/Mac/Linux, 不同版本)
CHROME_UA_POOL = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Mac Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

# Edge User-Agent 池
EDGE_UA_POOL = [
    # Windows Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Mac Edge
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Linux Edge
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# Firefox User-Agent 池 (备用)
FIREFOX_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# 混合池 (所有浏览器)
MIXED_UA_POOL = CHROME_UA_POOL + EDGE_UA_POOL + FIREFOX_UA_POOL

# 常见屏幕分辨率
SCREEN_RESOLUTIONS = [
    (1920, 1080),
    (1366, 768),
    (1536, 864),
    (1440, 900),
    (1280, 720),
    (1600, 900),
    (2560, 1440),
    (1280, 800),
    (1680, 1050),
    (1920, 1200),
]

# 常见语言设置
LANGUAGES = [
    ["zh-CN", "zh", "en"],
    ["zh-CN", "zh"],
    ["zh-TW", "zh", "en"],
    ["en-US", "en"],
    ["en-GB", "en"],
]

# 常见时区
TIMEZONES = [
    "Asia/Shanghai",
    "Asia/Hong_Kong",
    "Asia/Taipei",
    "Asia/Tokyo",
    "America/New_York",
    "America/Los_Angeles",
    "Europe/London",
]

# WebGL 厂商和渲染器组合
WEBGL_VENDORS = [
    ("Intel Inc.", "Intel Iris OpenGL Engine"),
    ("Intel Inc.", "Intel(R) UHD Graphics 630"),
    ("NVIDIA Corporation", "NVIDIA GeForce GTX 1080/PCIe/SSE2"),
    ("NVIDIA Corporation", "NVIDIA GeForce RTX 3080/PCIe/SSE2"),
    ("AMD", "AMD Radeon RX 580"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"),
]


def get_random_ua(browser: Optional[str] = None) -> str:
    """
    获取随机 User-Agent

    Args:
        browser: 浏览器类型 (chrome/edge/firefox/mixed)，None 表示混合

    Returns:
        随机选择的 User-Agent 字符串
    """
    if browser == "chrome":
        return random.choice(CHROME_UA_POOL)
    elif browser == "edge":
        return random.choice(EDGE_UA_POOL)
    elif browser == "firefox":
        return random.choice(FIREFOX_UA_POOL)
    else:
        return random.choice(MIXED_UA_POOL)


def get_random_resolution() -> tuple:
    """获取随机屏幕分辨率"""
    return random.choice(SCREEN_RESOLUTIONS)


def get_random_language() -> list:
    """获取随机语言设置"""
    return random.choice(LANGUAGES)


def get_random_timezone() -> str:
    """获取随机时区"""
    return random.choice(TIMEZONES)


def get_random_webgl_info() -> tuple:
    """获取随机 WebGL 厂商和渲染器"""
    return random.choice(WEBGL_VENDORS)


class UARotator:
    """User-Agent 轮换器"""

    def __init__(self, browser: Optional[str] = None, shuffle: bool = True):
        """
        初始化轮换器

        Args:
            browser: 浏览器类型
            shuffle: 是否打乱顺序
        """
        if browser == "chrome":
            self.pool = CHROME_UA_POOL.copy()
        elif browser == "edge":
            self.pool = EDGE_UA_POOL.copy()
        elif browser == "firefox":
            self.pool = FIREFOX_UA_POOL.copy()
        else:
            self.pool = MIXED_UA_POOL.copy()

        if shuffle:
            random.shuffle(self.pool)

        self.index = 0

    def next(self) -> str:
        """获取下一个 User-Agent"""
        ua = self.pool[self.index]
        self.index = (self.index + 1) % len(self.pool)
        return ua

    def reset(self):
        """重置到开头"""
        self.index = 0

    def __len__(self) -> int:
        return len(self.pool)
