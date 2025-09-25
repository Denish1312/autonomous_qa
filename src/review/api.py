"""
API endpoints for the QA review system.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from .models import TestCase, TestReview, ReviewStats
from .service import ReviewService

router = APIRouter(prefix="/review", tags=["review"])
service = ReviewService()

@router.post("/queue", response_model=TestCase)
async def queue_test_for_review(test_case: dict):
    """Queue a test case for review"""
    try:
        return await service.queue_for_review(test_case)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/pending", response_model=List[TestCase])
async def get_pending_reviews():
    """Get all test cases pending review"""
    return await service.get_pending_reviews()

@router.post("/submit", response_model=TestCase)
async def submit_review(review: TestReview):
    """Submit a review for a test case"""
    try:
        return await service.submit_review(review)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats", response_model=ReviewStats)
async def get_review_stats():
    """Get review statistics"""
    return await service.get_review_stats()
