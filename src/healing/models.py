"""
Models for the self-healing test mechanism.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Set
from enum import Enum
from datetime import datetime

class LocatorType(str, Enum):
    """Types of element locators"""
    ID = "id"
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    ARIA = "aria"
    TEST_ID = "data-testid"
    CLASS = "class"
    NAME = "name"

class ElementAttributes(BaseModel):
    """Model for storing element attributes"""
    tag_name: str
    id: Optional[str] = None
    class_names: Set[str] = Field(default_factory=set)
    name: Optional[str] = None
    text_content: Optional[str] = None
    aria_label: Optional[str] = None
    test_id: Optional[str] = None
    href: Optional[str] = None
    type: Optional[str] = None
    placeholder: Optional[str] = None
    value: Optional[str] = None
    role: Optional[str] = None

class ElementSnapshot(BaseModel):
    """Snapshot of an element's state"""
    locator: str
    locator_type: LocatorType
    attributes: ElementAttributes
    xpath_path: str
    parent_chain: List[ElementAttributes]
    timestamp: datetime = Field(default_factory=datetime.now)

class HealingAttempt(BaseModel):
    """Record of a healing attempt"""
    original_locator: str
    healed_locator: Optional[str]
    success: bool
    strategy_used: str
    confidence_score: float
    timestamp: datetime = Field(default_factory=datetime.now)

class HealingHistory(BaseModel):
    """History of healing attempts for a locator"""
    original_locator: str
    element_snapshot: ElementSnapshot
    healing_attempts: List[HealingAttempt] = []
    last_successful_locator: Optional[str] = None
    last_success_timestamp: Optional[datetime] = None

class HealingStats(BaseModel):
    """Statistics for healing attempts"""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    strategy_success_rates: Dict[str, float] = Field(default_factory=dict)
    average_confidence_score: float = 0.0
    healing_history: List[HealingHistory] = []
