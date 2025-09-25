"""
Service layer for the QA review system.
"""

from typing import List, Dict, Optional
from datetime import datetime
from .models import TestCase, TestReview, ReviewStats, ReviewStatus, FeedbackType
import json
import os
from pathlib import Path

class ReviewService:
    def __init__(self, storage_path: str = "./data/reviews"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.test_cases: Dict[str, TestCase] = self._load_test_cases()
        
    def _load_test_cases(self) -> Dict[str, TestCase]:
        """Load test cases from storage"""
        test_cases = {}
        if (self.storage_path / "test_cases.json").exists():
            with open(self.storage_path / "test_cases.json", "r") as f:
                data = json.load(f)
                for tc in data:
                    test_cases[tc["id"]] = TestCase(**tc)
        return test_cases
    
    def _save_test_cases(self):
        """Save test cases to storage"""
        with open(self.storage_path / "test_cases.json", "w") as f:
            json.dump([tc.dict() for tc in self.test_cases.values()], f, default=str)
    
    async def queue_for_review(self, test_case: Dict) -> TestCase:
        """Queue a new test case for review"""
        tc = TestCase(
            id=test_case["id"],
            title=test_case["title"],
            category=test_case["category"],
            steps=test_case["steps"],
            expected_result=test_case["expected_result"]
        )
        self.test_cases[tc.id] = tc
        self._save_test_cases()
        return tc
    
    async def get_pending_reviews(self) -> List[TestCase]:
        """Get all test cases pending review"""
        return [
            tc for tc in self.test_cases.values()
            if tc.review_status == ReviewStatus.PENDING
        ]
    
    async def submit_review(self, review: TestReview) -> TestCase:
        """Submit a review for a test case"""
        if review.test_id not in self.test_cases:
            raise ValueError(f"Test case {review.test_id} not found")
        
        test_case = self.test_cases[review.test_id]
        test_case.reviews.append(review)
        test_case.review_status = review.status
        test_case.updated_at = datetime.now()
        
        if review.suggested_changes:
            # Apply suggested changes
            for field, value in review.suggested_changes.items():
                if hasattr(test_case, field):
                    setattr(test_case, field, value)
        
        self._save_test_cases()
        return test_case
    
    async def get_review_stats(self) -> ReviewStats:
        """Get review statistics"""
        total = len([r for tc in self.test_cases.values() for r in tc.reviews])
        approved = len([r for tc in self.test_cases.values() 
                       for r in tc.reviews if r.status == ReviewStatus.APPROVED])
        rejected = len([r for tc in self.test_cases.values() 
                       for r in tc.reviews if r.status == ReviewStatus.REJECTED])
        needs_changes = len([r for tc in self.test_cases.values() 
                           for r in tc.reviews if r.status == ReviewStatus.NEEDS_CHANGES])
        
        # Calculate average rating
        ratings = [r.rating for tc in self.test_cases.values() for r in tc.reviews]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Count feedback by type
        feedback_counts = {}
        for tc in self.test_cases.values():
            for review in tc.reviews:
                for ft in review.feedback_type:
                    feedback_counts[ft] = feedback_counts.get(ft, 0) + 1
        
        return ReviewStats(
            total_reviews=total,
            approved_count=approved,
            rejected_count=rejected,
            needs_changes_count=needs_changes,
            average_rating=avg_rating,
            feedback_by_type=feedback_counts
        )
