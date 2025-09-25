"""
Parallel test execution service for multi-browser testing.
"""

from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
from .models import (
    BrowserType, BrowserConfig, BrowserContextConfig,
    DeviceConfig, BrowserTestResult, ParallelConfig,
    DEVICE_PROFILES
)
from .manager import BrowserManager
from ..healing.integration import HealingTestExecutor

class ParallelTestExecutor:
    """Executes tests in parallel across multiple browsers"""
    
    def __init__(
        self,
        config: Optional[ParallelConfig] = None,
        artifacts_path: str = "./artifacts"
    ):
        self.config = config or ParallelConfig()
        self.browser_manager = BrowserManager(artifacts_path)
        self.healing_executor = HealingTestExecutor()
    
    async def _execute_test_case(
        self,
        test_case: Dict[str, Any],
        browser_type: BrowserType,
        device_config: Optional[DeviceConfig] = None
    ) -> BrowserTestResult:
        """Execute a single test case in a specific browser"""
        started_at = datetime.now()
        context = None
        
        try:
            # Create browser context
            context = await self.browser_manager.create_context(
                browser_type,
                device_config=device_config
            )
            
            # Start tracing
            await self.browser_manager.start_tracing(
                context,
                browser_type,
                f"test_{test_case['id']}"
            )
            
            # Execute test with healing capability
            success = await self.healing_executor.execute_test_case(
                context.pages[0],
                test_case
            )
            
            # Take screenshot
            screenshot_path = await self.browser_manager.take_screenshot(
                context,
                f"test_{test_case['id']}",
                browser_type
            )
            
            # Stop tracing
            trace_path = await self.browser_manager.stop_tracing(
                context,
                browser_type,
                f"test_{test_case['id']}"
            )
            
            # Get video path if recording enabled
            video_path = self.browser_manager.get_video_path(context.id)
            
            # Get HAR path if recording enabled
            har_path = self.browser_manager.get_har_path(context.id)
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds() * 1000
            
            return BrowserTestResult(
                browser_type=browser_type,
                device_name=device_config.name if device_config else None,
                status="passed" if success else "failed",
                duration_ms=int(duration),
                screenshot_path=screenshot_path,
                video_path=video_path,
                trace_path=trace_path,
                har_path=har_path,
                started_at=started_at,
                completed_at=completed_at
            )
            
        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds() * 1000
            
            return BrowserTestResult(
                browser_type=browser_type,
                device_name=device_config.name if device_config else None,
                status="error",
                duration_ms=int(duration),
                error_message=str(e),
                started_at=started_at,
                completed_at=completed_at
            )
            
        finally:
            if context:
                await self.browser_manager.close_context(context.id)
    
    async def _execute_with_retry(
        self,
        test_case: Dict[str, Any],
        browser_type: BrowserType,
        device_config: Optional[DeviceConfig] = None
    ) -> BrowserTestResult:
        """Execute a test case with retry logic"""
        result = await self._execute_test_case(test_case, browser_type, device_config)
        
        if (
            result.status in ["failed", "error"]
            and self.config.retry_failed
            and self.config.max_retries > 0
        ):
            for retry in range(self.config.max_retries):
                # Wait before retry
                await asyncio.sleep(self.config.retry_delay_ms / 1000)
                
                retry_result = await self._execute_test_case(
                    test_case,
                    browser_type,
                    device_config
                )
                
                if retry_result.status == "passed":
                    return retry_result
                
                result = retry_result
        
        return result
    
    async def execute_test_suite(
        self,
        test_cases: List[Dict[str, Any]],
        browser_types: Optional[List[BrowserType]] = None,
        device_profiles: Optional[List[str]] = None
    ) -> Dict[str, List[BrowserTestResult]]:
        """
        Execute a test suite across multiple browsers and devices in parallel.
        Returns results grouped by test case ID.
        """
        browser_types = browser_types or [BrowserType.CHROMIUM]
        device_profiles = device_profiles or ["Desktop HD"]
        
        results: Dict[str, List[BrowserTestResult]] = {}
        
        # Create all test combinations
        test_combinations = []
        for test_case in test_cases:
            for browser_type in browser_types:
                for profile_name in device_profiles:
                    device_config = DEVICE_PROFILES.get(profile_name)
                    test_combinations.append((test_case, browser_type, device_config))
        
        # Execute tests in parallel with concurrency limit
        semaphore = asyncio.Semaphore(self.config.max_parallel_instances)
        
        async def execute_with_semaphore(combination):
            async with semaphore:
                test_case, browser_type, device_config = combination
                return (
                    test_case["id"],
                    await self._execute_with_retry(
                        test_case,
                        browser_type,
                        device_config
                    )
                )
        
        # Run all test combinations
        execution_tasks = [
            execute_with_semaphore(combination)
            for combination in test_combinations
        ]
        
        execution_results = await asyncio.gather(*execution_tasks)
        
        # Group results by test case ID
        for test_id, result in execution_results:
            if test_id not in results:
                results[test_id] = []
            results[test_id].append(result)
        
        return results
    
    async def cleanup(self):
        """Clean up browser instances and contexts"""
        await self.browser_manager.close_all()
