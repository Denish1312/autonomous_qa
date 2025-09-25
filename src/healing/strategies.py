"""
Implementation of different healing strategies for test automation.
"""

from typing import Optional, List, Tuple
import difflib
from playwright.sync_api import Page, Locator
from .models import ElementSnapshot, LocatorType, ElementAttributes
import re
from bs4 import BeautifulSoup

class BaseStrategy:
    """Base class for healing strategies"""
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        
    async def heal(self, page: Page, snapshot: ElementSnapshot) -> Tuple[Optional[str], float]:
        """
        Attempt to heal a broken locator.
        Returns: (healed_locator, confidence_score)
        """
        raise NotImplementedError

class TextSimilarityStrategy(BaseStrategy):
    """Heal by finding elements with similar text content"""
    def __init__(self):
        super().__init__("text_similarity", weight=0.8)
    
    async def heal(self, page: Page, snapshot: ElementSnapshot) -> Tuple[Optional[str], float]:
        try:
            # Get all text content from the page
            all_text_content = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('*'))
                    .map(el => ({
                        text: el.textContent,
                        tag: el.tagName.toLowerCase(),
                        id: el.id,
                        classes: Array.from(el.classList)
                    }));
            }""")
            
            target_text = snapshot.attributes.text_content
            if not target_text:
                return None, 0.0
                
            # Find best match
            best_match = None
            best_score = 0.0
            
            for element in all_text_content:
                if not element['text']:
                    continue
                    
                score = difflib.SequenceMatcher(None, target_text, element['text']).ratio()
                
                # Boost score if tag name matches
                if element['tag'] == snapshot.attributes.tag_name:
                    score *= 1.2
                    
                # Boost score if some classes match
                common_classes = set(element['classes']) & snapshot.attributes.class_names
                if common_classes:
                    score *= (1 + 0.1 * len(common_classes))
                
                if score > best_score:
                    best_score = score
                    best_match = element
            
            if best_match and best_score > 0.7:
                # Create appropriate locator based on best match
                if best_match['id']:
                    return f"#{best_match['id']}", best_score
                return f"//*[contains(text(), '{target_text}')]", best_score * 0.9
                
            return None, 0.0
            
        except Exception as e:
            print(f"Error in TextSimilarityStrategy: {str(e)}")
            return None, 0.0

class AttributeBasedStrategy(BaseStrategy):
    """Heal by matching element attributes"""
    def __init__(self):
        super().__init__("attribute_based", weight=0.9)
    
    async def heal(self, page: Page, snapshot: ElementSnapshot) -> Tuple[Optional[str], float]:
        try:
            # Build a complex CSS selector based on available attributes
            selectors = []
            confidence = 0.0
            
            # Start with tag name
            selector_parts = [snapshot.attributes.tag_name]
            confidence += 0.1
            
            # Add class names
            if snapshot.attributes.class_names:
                selector_parts.extend(f".{cls}" for cls in snapshot.attributes.class_names)
                confidence += 0.2
            
            # Add other attributes
            if snapshot.attributes.test_id:
                selector_parts.append(f"[data-testid='{snapshot.attributes.test_id}']")
                confidence += 0.3
                
            if snapshot.attributes.name:
                selector_parts.append(f"[name='{snapshot.attributes.name}']")
                confidence += 0.2
                
            if snapshot.attributes.role:
                selector_parts.append(f"[role='{snapshot.attributes.role}']")
                confidence += 0.2
                
            # Combine into CSS selector
            selector = ''.join(selector_parts)
            
            # Verify the selector finds exactly one element
            count = await page.evaluate(f"document.querySelectorAll('{selector}').length")
            
            if count == 1:
                return selector, min(confidence, 1.0)
            elif count > 1:
                # Try to make it more specific
                if snapshot.attributes.text_content:
                    selector += f":contains('{snapshot.attributes.text_content}')"
                    count = await page.evaluate(f"document.querySelectorAll('{selector}').length")
                    if count == 1:
                        return selector, min(confidence * 0.9, 1.0)
                        
            return None, 0.0
            
        except Exception as e:
            print(f"Error in AttributeBasedStrategy: {str(e)}")
            return None, 0.0

class XPathStrategy(BaseStrategy):
    """Heal by generating relative XPath"""
    def __init__(self):
        super().__init__("xpath", weight=0.7)
    
    async def heal(self, page: Page, snapshot: ElementSnapshot) -> Tuple[Optional[str], float]:
        try:
            # Start with the most specific attributes
            if snapshot.attributes.id:
                xpath = f"//{snapshot.attributes.tag_name}[@id='{snapshot.attributes.id}']"
                return xpath, 1.0
                
            # Build XPath based on parent chain
            xpath_parts = []
            confidence = 0.0
            
            for parent in snapshot.parent_chain:
                part = f"//{parent.tag_name}"
                conditions = []
                
                if parent.class_names:
                    conditions.append(f"contains(@class, '{' '.join(parent.class_names)}')")
                    confidence += 0.1
                    
                if parent.text_content:
                    conditions.append(f"contains(text(), '{parent.text_content}')")
                    confidence += 0.2
                    
                if conditions:
                    part += f"[{' and '.join(conditions)}]"
                    
                xpath_parts.append(part)
            
            # Add target element
            target_part = f"//{snapshot.attributes.tag_name}"
            conditions = []
            
            if snapshot.attributes.class_names:
                conditions.append(f"contains(@class, '{' '.join(snapshot.attributes.class_names)}')")
                confidence += 0.2
                
            if snapshot.attributes.text_content:
                conditions.append(f"contains(text(), '{snapshot.attributes.text_content}')")
                confidence += 0.3
                
            if conditions:
                target_part += f"[{' and '.join(conditions)}]"
                
            xpath_parts.append(target_part)
            
            # Combine XPath parts
            xpath = "".join(xpath_parts)
            
            # Verify uniqueness
            count = await page.evaluate(f"document.evaluate('count({xpath})', document, null, XPathResult.NUMBER_TYPE, null).numberValue")
            
            if count == 1:
                return xpath, min(confidence, 1.0)
            return None, 0.0
            
        except Exception as e:
            print(f"Error in XPathStrategy: {str(e)}")
            return None, 0.0
