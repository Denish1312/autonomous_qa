"""
Browser management service for handling multiple browser instances.
"""

from typing import Dict, Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext
import asyncio
import os
from datetime import datetime
from pathlib import Path
from .models import (
    BrowserType, BrowserConfig, BrowserContextConfig,
    DeviceConfig, BrowserTestResult, DEFAULT_BROWSER_CONFIGS
)

class BrowserManager:
    """Manages browser instances and contexts"""
    
    def __init__(self, artifacts_path: str = "./artifacts"):
        self.artifacts_path = Path(artifacts_path)
        self.browsers: Dict[BrowserType, Browser] = {}
        self.contexts: Dict[str, BrowserContext] = {}
        
        # Create artifact directories
        for browser_type in BrowserType:
            (self.artifacts_path / "screenshots" / browser_type).mkdir(parents=True, exist_ok=True)
            (self.artifacts_path / "videos" / browser_type).mkdir(parents=True, exist_ok=True)
            (self.artifacts_path / "traces" / browser_type).mkdir(parents=True, exist_ok=True)
            (self.artifacts_path / "har" / browser_type).mkdir(parents=True, exist_ok=True)
    
    async def initialize_browser(
        self,
        browser_type: BrowserType,
        config: Optional[BrowserConfig] = None
    ) -> Browser:
        """Initialize a browser instance with the given configuration"""
        if browser_type in self.browsers:
            return self.browsers[browser_type]
        
        config = config or DEFAULT_BROWSER_CONFIGS[browser_type]
        
        async with async_playwright() as playwright:
            browser_launcher = getattr(playwright, browser_type.value)
            
            browser = await browser_launcher.launch(
                headless=config.headless,
                slow_mo=config.slow_mo,
                proxy={
                    "server": config.proxy
                } if config.proxy else None
            )
            
            self.browsers[browser_type] = browser
            return browser
    
    async def create_context(
        self,
        browser_type: BrowserType,
        context_config: Optional[BrowserContextConfig] = None,
        device_config: Optional[DeviceConfig] = None
    ) -> BrowserContext:
        """Create a new browser context with the given configuration"""
        browser = await self.initialize_browser(browser_type)
        config = context_config or BrowserContextConfig()
        device = device_config or None
        
        # Generate unique context ID
        context_id = f"{browser_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare context options
        context_options = {
            "record_video_dir": str(self.artifacts_path / "videos" / browser_type.value) if config.record_video else None,
            "record_har_path": str(self.artifacts_path / "har" / browser_type.value / f"{context_id}.har") if config.record_har else None,
            "ignore_https_errors": True,
            "bypass_csp": config.bypass_csp,
            "offline": config.offline,
            "color_scheme": config.color_scheme,
            "reduced_motion": config.reduced_motion,
            "force_dark": config.force_dark_mode
        }
        
        # Add device emulation if specified
        if device:
            context_options.update({
                "viewport": {
                    "width": device.viewport.width,
                    "height": device.viewport.height
                },
                "user_agent": device.user_agent,
                "device_scale_factor": device.device_scale_factor,
                "is_mobile": device.is_mobile,
                "has_touch": device.has_touch
            })
        
        context = await browser.new_context(**context_options)
        self.contexts[context_id] = context
        return context
    
    async def close_context(self, context_id: str):
        """Close a browser context"""
        if context_id in self.contexts:
            await self.contexts[context_id].close()
            del self.contexts[context_id]
    
    async def close_all(self):
        """Close all browser instances and contexts"""
        # Close all contexts
        for context_id in list(self.contexts.keys()):
            await self.close_context(context_id)
        
        # Close all browsers
        for browser in self.browsers.values():
            await browser.close()
        
        self.browsers.clear()
    
    async def take_screenshot(
        self,
        context: BrowserContext,
        name: str,
        browser_type: BrowserType
    ) -> str:
        """Take a screenshot in the given context"""
        page = context.pages[0]
        screenshot_path = str(
            self.artifacts_path / "screenshots" / browser_type.value / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        await page.screenshot(path=screenshot_path, full_page=True)
        return screenshot_path
    
    async def start_tracing(
        self,
        context: BrowserContext,
        browser_type: BrowserType,
        name: str
    ):
        """Start browser tracing"""
        await context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True,
            name=name
        )
    
    async def stop_tracing(
        self,
        context: BrowserContext,
        browser_type: BrowserType,
        name: str
    ) -> str:
        """Stop browser tracing and save the trace"""
        trace_path = str(
            self.artifacts_path / "traces" / browser_type.value / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        )
        await context.tracing.stop(path=trace_path)
        return trace_path
    
    def get_har_path(self, context_id: str) -> Optional[str]:
        """Get the HAR file path for a context"""
        if context_id in self.contexts:
            return str(self.artifacts_path / "har" / f"{context_id}.har")
        return None
    
    def get_video_path(self, context_id: str) -> Optional[str]:
        """Get the video recording path for a context"""
        if context_id in self.contexts:
            page = self.contexts[context_id].pages[0]
            return page.video.path() if page.video else None
        return None
