"""
Models for the QA review system.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"

class FeedbackType(str, Enum):
    TEST_QUALITY = "test_quality"
    COVERAGE = "coverage"
    CLARITY = "clarity"
    MAINTAINABILITY = "maintainability"

class TestReview(BaseModel):
    """Model for test case review submission"""
    test_id: str
    reviewer: str
    status: ReviewStatus
    feedback: Optional[str] = None
    suggested_changes: Optional[Dict[str, str]] = None
    feedback_type: List[FeedbackType]
    rating: int = Field(ge=1, le=5)
    review_date: datetime = Field(default_factory=datetime.now)

class TestCase(BaseModel):
    """Model for test case with review status"""
    id: str
    title: str
    category: str
    steps: List[str]
    expected_result: str
    review_status: ReviewStatus = ReviewStatus.PENDING
    reviews: List[TestReview] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ReviewStats(BaseModel):
    """Model for review statistics"""
    total_reviews: int
    approved_count: int
    rejected_count: int
    needs_changes_count: int
    average_rating: float
    feedback_by_type: Dict[FeedbackType, int]
