"""反爬虫检测模块 - 浏览器指纹伪装和人类行为模拟"""

import random
import time
from typing import Optional, Dict, Any

from .ua_pool import (
    get_random_ua,
    get_random_resolution,
    get_random_language,
    get_random_timezone,
    get_random_webgl_info,
)


# 隐身 JavaScript 脚本 - 用于绕过常见的反爬虫检测
STEALTH_JS = """
// 1. 隐藏 navigator.webdriver
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
    configurable: true
});

// 2. 伪装 navigator.plugins (非空)
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const plugins = [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
        ];
        plugins.length = 3;
        return plugins;
    },
    configurable: true
});

// 3. 伪装 navigator.languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en'],
    configurable: true
});

// 4. 伪装 navigator.platform
Object.defineProperty(navigator, 'platform', {
    get: () => 'Win32',
    configurable: true
});

// 5. 修复 Permissions API
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// 6. 隐藏 chrome.runtime (Headless 检测)
if (window.chrome) {
    window.chrome.runtime = {
        connect: () => {},
        sendMessage: () => {}
    };
}

// 7. 修复 iframe contentWindow
const originalContentWindow = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
    get: function() {
        const iframe = originalContentWindow.get.call(this);
        if (iframe) {
            try {
                Object.defineProperty(iframe.navigator, 'webdriver', {
                    get: () => undefined
                });
            } catch (e) {}
        }
        return iframe;
    }
});

// 8. 隐藏自动化相关的 window 属性
['__webdriver_script_fn', '__driver_evaluate', '__webdriver_evaluate',
 '__selenium_evaluate', '__fxdriver_evaluate', '__driver_unwrapped',
 '__webdriver_unwrapped', '__selenium_unwrapped', '__fxdriver_unwrapped',
 '_Selenium_IDE_Recorder', '_selenium', 'calledSelenium', '$cdc_',
 '$chrome_asyncScriptInfo', '__$webdriverAsyncExecutor', 'webdriver',
 '__webdriver_script_function'].forEach(prop => {
    try {
        delete window[prop];
        Object.defineProperty(window, prop, {
            get: () => undefined,
            configurable: true
        });
    } catch (e) {}
});

// 9. 覆盖 navigator.connection (模拟真实网络)
Object.defineProperty(navigator, 'connection', {
    get: () => ({
        effectiveType: '4g',
        rtt: 50,
        downlink: 10,
        saveData: false
    }),
    configurable: true
});

// 10. 添加 navigator.deviceMemory
Object.defineProperty(navigator, 'deviceMemory', {
    get: () => 8,
    configurable: true
});

// 11. 添加 navigator.hardwareConcurrency
Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => 8,
    configurable: true
});

console.log('[Stealth] Anti-detect scripts injected');
"""


# Canvas 指纹干扰脚本
CANVAS_FINGERPRINT_JS = """
// Canvas 指纹干扰 - 添加微小噪点
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

HTMLCanvasElement.prototype.toDataURL = function(type) {
    if (this.width > 16 && this.height > 16) {
        const ctx = this.getContext('2d');
        if (ctx) {
            const imageData = originalGetImageData.call(ctx, 0, 0, this.width, this.height);
            // 添加随机噪点
            for (let i = 0; i < imageData.data.length; i += 4) {
                if (Math.random() < 0.01) {  // 1% 的像素
                    imageData.data[i] = Math.max(0, Math.min(255, imageData.data[i] + Math.floor(Math.random() * 3) - 1));
                }
            }
            ctx.putImageData(imageData, 0, 0);
        }
    }
    return originalToDataURL.apply(this, arguments);
};

console.log('[Stealth] Canvas fingerprint protection enabled');
"""


# WebGL 指纹干扰脚本
def get_webgl_spoof_js(vendor: str, renderer: str) -> str:
    """生成 WebGL 指纹伪装脚本"""
    return f"""
// WebGL 指纹伪装
const getParameterProxyHandler = {{
    apply: function(target, ctx, args) {{
        const param = args[0];
        // UNMASKED_VENDOR_WEBGL
        if (param === 37445) {{
            return '{vendor}';
        }}
        // UNMASKED_RENDERER_WEBGL
        if (param === 37446) {{
            return '{renderer}';
        }}
        return Reflect.apply(target, ctx, args);
    }}
}};

// 拦截 WebGL getParameter
const webglGetParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = new Proxy(webglGetParameter, getParameterProxyHandler);

// WebGL2 同样处理
if (typeof WebGL2RenderingContext !== 'undefined') {{
    const webgl2GetParameter = WebGL2RenderingContext.prototype.getParameter;
    WebGL2RenderingContext.prototype.getParameter = new Proxy(webgl2GetParameter, getParameterProxyHandler);
}}

console.log('[Stealth] WebGL fingerprint spoofed');
"""


# AudioContext 指纹干扰脚本
AUDIO_FINGERPRINT_JS = """
// AudioContext 指纹干扰
const originalCreateOscillator = AudioContext.prototype.createOscillator;
const originalCreateDynamicsCompressor = AudioContext.prototype.createDynamicsCompressor;

AudioContext.prototype.createOscillator = function() {
    const oscillator = originalCreateOscillator.apply(this, arguments);
    const originalConnect = oscillator.connect.bind(oscillator);
    oscillator.connect = function(destination) {
        if (destination.context) {
            // 添加微小的频率偏移
            oscillator.frequency.value += (Math.random() - 0.5) * 0.01;
        }
        return originalConnect(destination);
    };
    return oscillator;
};

console.log('[Stealth] Audio fingerprint protection enabled');
"""


class AntiDetect:
    """反爬虫检测类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化反爬虫配置

        Args:
            config: 配置字典，支持的选项：
                - stealth: bool, 启用隐身模式 (默认 True)
                - random_ua: bool, 随机 User-Agent (默认 True)
                - random_window: bool, 随机窗口尺寸 (默认 True)
                - canvas_protect: bool, Canvas 指纹保护 (默认 True)
                - webgl_spoof: bool, WebGL 指纹伪装 (默认 True)
                - audio_protect: bool, 音频指纹保护 (默认 False)
                - proxy: str, 代理服务器地址
                - human_delay: bool, 人类行为延迟 (默认 True)
        """
        self.config = config or {}

        # 默认配置
        self.stealth = self.config.get("stealth", True)
        self.random_ua = self.config.get("random_ua", True)
        self.random_window = self.config.get("random_window", True)
        self.canvas_protect = self.config.get("canvas_protect", True)
        self.webgl_spoof = self.config.get("webgl_spoof", True)
        self.audio_protect = self.config.get("audio_protect", False)
        self.proxy = self.config.get("proxy")
        self.human_delay = self.config.get("human_delay", True)

    def apply_to_options(self, options, browser: str = "chrome"):
        """
        将反爬虫配置应用到浏览器选项

        Args:
            options: Selenium 浏览器选项对象
            browser: 浏览器类型 (chrome/edge)
        """
        # 基础隐身参数
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # 禁用自动化扩展
        options.add_argument("--disable-extensions")

        # 禁用信息栏
        options.add_argument("--disable-infobars")

        # 禁用 GPU 加速（可选，某些情况下有帮助）
        # options.add_argument("--disable-gpu")

        # 设置语言
        languages = get_random_language()
        options.add_argument(f"--lang={languages[0]}")

        # 代理设置
        if self.proxy:
            options.add_argument(f"--proxy-server={self.proxy}")

        # 随机 User-Agent
        if self.random_ua:
            ua = get_random_ua(browser)
            options.add_argument(f"--user-agent={ua}")

        # Chrome 特有的实验性选项
        if browser == "chrome":
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            # 禁用日志
            options.add_experimental_option("excludeSwitches", ["enable-logging"])

            # 设置偏好
            prefs = {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.default_content_setting_values.notifications": 2,
            }
            options.add_experimental_option("prefs", prefs)

        # Edge 特有选项
        elif browser == "edge":
            # Edge 使用类似的选项
            try:
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
            except Exception:
                pass  # Edge 某些版本可能不支持

    def inject_stealth_scripts(self, driver):
        """
        注入隐身脚本到浏览器

        Args:
            driver: Selenium WebDriver 实例
        """
        scripts_to_inject = []

        # 主隐身脚本
        if self.stealth:
            scripts_to_inject.append(STEALTH_JS)

        # Canvas 指纹保护
        if self.canvas_protect:
            scripts_to_inject.append(CANVAS_FINGERPRINT_JS)

        # WebGL 指纹伪装
        if self.webgl_spoof:
            vendor, renderer = get_random_webgl_info()
            scripts_to_inject.append(get_webgl_spoof_js(vendor, renderer))

        # 音频指纹保护
        if self.audio_protect:
            scripts_to_inject.append(AUDIO_FINGERPRINT_JS)

        # 使用 CDP 在页面加载前注入脚本
        combined_script = "\n".join(scripts_to_inject)

        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": combined_script}
            )
        except Exception:
            # 如果 CDP 不支持，在页面加载后执行
            try:
                driver.execute_script(combined_script)
            except Exception:
                pass

    def randomize_window(self, driver):
        """
        随机化窗口尺寸

        Args:
            driver: Selenium WebDriver 实例
        """
        if self.random_window:
            width, height = get_random_resolution()
            # 添加一些随机偏移
            width += random.randint(-50, 50)
            height += random.randint(-30, 30)
            driver.set_window_size(width, height)

            # 随机窗口位置
            x = random.randint(0, 200)
            y = random.randint(0, 100)
            try:
                driver.set_window_position(x, y)
            except Exception:
                pass

    def human_like_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """
        人类行为延迟

        Args:
            min_sec: 最小延迟秒数
            max_sec: 最大延迟秒数
        """
        if self.human_delay:
            delay = random.uniform(min_sec, max_sec)
            time.sleep(delay)

    def human_like_typing(self, element, text: str, min_delay: float = 0.05, max_delay: float = 0.15):
        """
        模拟人类打字速度

        Args:
            element: 输入元素
            text: 要输入的文本
            min_delay: 每个字符的最小延迟
            max_delay: 每个字符的最大延迟
        """
        if not self.human_delay:
            element.send_keys(text)
            return

        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))

            # 偶尔停顿更长时间（模拟思考）
            if random.random() < 0.05:
                time.sleep(random.uniform(0.3, 0.8))

    def random_scroll(self, driver, times: int = 1):
        """
        随机滚动页面

        Args:
            driver: Selenium WebDriver 实例
            times: 滚动次数
        """
        for _ in range(times):
            # 随机滚动距离
            scroll_distance = random.randint(100, 500)
            direction = random.choice([1, -1])

            driver.execute_script(f"window.scrollBy(0, {scroll_distance * direction});")
            time.sleep(random.uniform(0.3, 1.0))

    def random_mouse_movement(self, driver):
        """
        模拟随机鼠标移动（使用 JavaScript）

        Args:
            driver: Selenium WebDriver 实例
        """
        js_mouse_move = """
        const event = new MouseEvent('mousemove', {
            'view': window,
            'bubbles': true,
            'cancelable': true,
            'clientX': arguments[0],
            'clientY': arguments[1]
        });
        document.dispatchEvent(event);
        """

        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            try:
                driver.execute_script(js_mouse_move, x, y)
                time.sleep(random.uniform(0.1, 0.3))
            except Exception:
                pass


def create_stealth_driver(headless: bool = False, browser: str = "chrome",
                          anti_detect_config: Optional[Dict[str, Any]] = None):
    """
    创建带有反爬虫检测的 WebDriver

    Args:
        headless: 是否使用无头模式
        browser: 浏览器类型 (chrome/edge)
        anti_detect_config: 反爬虫配置

    Returns:
        配置好的 WebDriver 实例
    """
    from selenium import webdriver
    import platform
    from pathlib import Path

    anti_detect = AntiDetect(anti_detect_config)
    drivers_dir = Path(__file__).parents[4] / "drivers"

    if browser == "edge":
        from selenium.webdriver.edge.options import Options
        from selenium.webdriver.edge.service import Service

        options = Options()
        if headless:
            options.add_argument("--headless")

        # 应用反爬虫配置
        anti_detect.apply_to_options(options, "edge")

        driver_path = drivers_dir / ("msedgedriver.exe" if platform.system() == "Windows" else "msedgedriver")
        if driver_path.exists():
            service = Service(str(driver_path))
            driver = webdriver.Edge(service=service, options=options)
        else:
            driver = webdriver.Edge(options=options)

    else:  # chrome
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        options = Options()
        if headless:
            options.add_argument("--headless=new")  # 新版 headless

        # 应用反爬虫配置
        anti_detect.apply_to_options(options, "chrome")

        driver_path = drivers_dir / ("chromedriver.exe" if platform.system() == "Windows" else "chromedriver")
        if driver_path.exists():
            service = Service(str(driver_path))
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)

    # 注入隐身脚本
    anti_detect.inject_stealth_scripts(driver)

    # 随机化窗口
    anti_detect.randomize_window(driver)

    return driver, anti_detect
