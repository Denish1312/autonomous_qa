"""
Integration of the self-healing mechanism with test execution.
"""

from typing import Dict, Any, Optional
from playwright.sync_api import Page
import re
from .service import HealingService
from .models import ElementSnapshot, ElementAttributes, LocatorType

class HealingTestExecutor:
    def __init__(self):
        self.healing_service = HealingService()
        
    async def _capture_element_snapshot(
        self,
        page: Page,
        locator: str
    ) -> Optional[ElementSnapshot]:
        """Capture a snapshot of an element's state"""
        try:
            # Get element information
            element_info = await page.evaluate(f"""(locator) => {{
                const element = document.querySelector(locator);
                if (!element) return null;
                
                return {{
                    tagName: element.tagName.toLowerCase(),
                    id: element.id,
                    classList: Array.from(element.classList),
                    name: element.getAttribute('name'),
                    textContent: element.textContent,
                    ariaLabel: element.getAttribute('aria-label'),
                    testId: element.getAttribute('data-testid'),
                    href: element.getAttribute('href'),
                    type: element.getAttribute('type'),
                    placeholder: element.getAttribute('placeholder'),
                    value: element.value,
                    role: element.getAttribute('role'),
                    xpath: document.evaluate(
                        'ancestor-or-self::*',
                        element,
                        null,
                        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                        null
                    )
                }};
            }}""", locator)
            
            if not element_info:
                return None
                
            # Create element attributes
            attributes = ElementAttributes(
                tag_name=element_info["tagName"],
                id=element_info["id"],
                class_names=set(element_info["classList"]),
                name=element_info["name"],
                text_content=element_info["textContent"],
                aria_label=element_info["ariaLabel"],
                test_id=element_info["testId"],
                href=element_info["href"],
                type=element_info["type"],
                placeholder=element_info["placeholder"],
                value=element_info["value"],
                role=element_info["role"]
            )
            
            # Determine locator type
            locator_type = LocatorType.CSS
            if locator.startswith("//"):
                locator_type = LocatorType.XPATH
            elif locator.startswith("#"):
                locator_type = LocatorType.ID
            elif locator.startswith("[data-testid="):
                locator_type = LocatorType.TEST_ID
            
            return ElementSnapshot(
                locator=locator,
                locator_type=locator_type,
                attributes=attributes,
                xpath_path=element_info["xpath"],
                parent_chain=[]  # TODO: Implement parent chain capture
            )
            
        except Exception as e:
            print(f"Error capturing element snapshot: {str(e)}")
            return None
    
    async def execute_test_step(
        self,
        page: Page,
        step: str,
        retries: int = 2
    ) -> bool:
        """
        Execute a test step with self-healing capability.
        Returns True if step executed successfully.
        """
        # Extract locator from step
        locator_match = re.search(r'(#[\w-]+|//[^"]+|\.[\w-]+|\[.*?\])', step)
        if not locator_match:
            # No locator in step, execute as is
            try:
                await page.evaluate(f"() => {{ {step} }}")
                return True
            except:
                return False
        
        original_locator = locator_match.group(1)
        
        for attempt in range(retries + 1):
            try:
                if attempt == 0:
                    # Try original locator first
                    element = await page.wait_for_selector(original_locator, timeout=1000)
                    if element:
                        # Execute step
                        await page.evaluate(step)
                        return True
                else:
                    # Capture element snapshot for healing
                    snapshot = await self._capture_element_snapshot(page, original_locator)
                    if not snapshot:
                        continue
                    
                    # Attempt to heal
                    healed_locator, confidence = await self.healing_service.heal_locator(
                        page, original_locator, snapshot
                    )
                    
                    if healed_locator and confidence > 0.7:
                        # Update step with healed locator
                        healed_step = step.replace(original_locator, healed_locator)
                        
                        # Execute healed step
                        await page.evaluate(healed_step)
                        return True
            
            except Exception as e:
                print(f"Error executing step (attempt {attempt + 1}): {str(e)}")
                if attempt == retries:
                    return False
                continue
        
        return False
    
    async def execute_test_case(self, page: Page, test_case: Dict[str, Any]) -> bool:
        """
        Execute a test case with self-healing capability.
        Returns True if all steps executed successfully.
        """
        success = True
        for step in test_case["steps"]:
            if not await self.execute_test_step(page, step):
                success = False
                break
        return success
