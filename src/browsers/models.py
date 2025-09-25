"""
Models for multi-browser test execution configuration.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Set
from enum import Enum
from datetime import datetime

class BrowserType(str, Enum):
    """Supported browser types"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"

class DeviceType(str, Enum):
    """Device types for responsive testing"""
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"

class ViewportSize(BaseModel):
    """Viewport dimensions"""
    width: int
    height: int

class DeviceConfig(BaseModel):
    """Device-specific configuration"""
    name: str
    viewport: ViewportSize
    user_agent: str
    device_scale_factor: float = 1.0
    is_mobile: bool = False
    has_touch: bool = False
    is_landscape: bool = False

class BrowserConfig(BaseModel):
    """Browser-specific configuration"""
    browser_type: BrowserType
    headless: bool = True
    slow_mo: Optional[int] = None
    ignore_https_errors: bool = False
    proxy: Optional[str] = None
    downloads_path: Optional[str] = None
    traces_path: Optional[str] = None
    viewport: Optional[ViewportSize] = None
    locale: str = "en-US"
    timezone: str = "UTC"
    geolocation: Optional[Dict[str, float]] = None
    permissions: Set[str] = set()
    extra_http_headers: Dict[str, str] = {}

class BrowserContextConfig(BaseModel):
    """Configuration for a browser context"""
    device: Optional[DeviceConfig] = None
    record_video: bool = False
    record_har: bool = False
    ignore_js_errors: bool = False
    bypass_csp: bool = False
    offline: bool = False
    color_scheme: str = "light"
    reduced_motion: str = "no-preference"
    force_dark_mode: bool = False

class ParallelConfig(BaseModel):
    """Configuration for parallel test execution"""
    max_parallel_instances: int = 4
    retry_failed: bool = True
    max_retries: int = 2
    retry_delay_ms: int = 1000
    timeout_ms: int = 30000

class BrowserTestResult(BaseModel):
    """Result of a browser test execution"""
    browser_type: BrowserType
    device_name: Optional[str]
    status: str
    duration_ms: int
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    trace_path: Optional[str] = None
    har_path: Optional[str] = None
    logs: List[str] = []
    started_at: datetime
    completed_at: datetime

# Pre-configured device profiles
DEVICE_PROFILES = {
    "Desktop HD": DeviceConfig(
        name="Desktop HD",
        viewport=ViewportSize(width=1920, height=1080),
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        device_scale_factor=1.0,
        is_mobile=False,
        has_touch=False,
        is_landscape=True
    ),
    "iPad Pro": DeviceConfig(
        name="iPad Pro",
        viewport=ViewportSize(width=1024, height=1366),
        user_agent="Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        device_scale_factor=2.0,
        is_mobile=True,
        has_touch=True,
        is_landscape=False
    ),
    "iPhone 12": DeviceConfig(
        name="iPhone 12",
        viewport=ViewportSize(width=390, height=844),
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        device_scale_factor=3.0,
        is_mobile=True,
        has_touch=True,
        is_landscape=False
    )
}

# Default browser configurations
DEFAULT_BROWSER_CONFIGS = {
    BrowserType.CHROMIUM: BrowserConfig(
        browser_type=BrowserType.CHROMIUM,
        headless=True,
        viewport=ViewportSize(width=1280, height=720),
        ignore_https_errors=True,
        traces_path="./artifacts/traces/chromium"
    ),
    BrowserType.FIREFOX: BrowserConfig(
        browser_type=BrowserType.FIREFOX,
        headless=True,
        viewport=ViewportSize(width=1280, height=720),
        ignore_https_errors=True,
        traces_path="./artifacts/traces/firefox"
    ),
    BrowserType.WEBKIT: BrowserConfig(
        browser_type=BrowserType.WEBKIT,
        headless=True,
        viewport=ViewportSize(width=1280, height=720),
        ignore_https_errors=True,
        traces_path="./artifacts/traces/webkit"
    )
}
