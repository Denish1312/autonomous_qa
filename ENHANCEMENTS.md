# Autonomous QA System - Enhancement Plan

## 1. Self-Healing Test Framework

### Implementation in `src/agent/healing.py`:
```python
from playwright.sync_api import Page
from typing import Dict, List, Optional
import difflib
import re

class SmartLocator:
    def __init__(self):
        self.locator_history: Dict[str, List[str]] = {}
        self.similarity_threshold = 0.8

    async def find_element(self, page: Page, original_selector: str) -> Optional[str]:
        """
        Smart element location using multiple strategies.
        Falls back to AI-powered element detection if needed.
        """
        # Try exact match first
        try:
            element = await page.wait_for_selector(original_selector, timeout=1000)
            if element:
                return original_selector
        except:
            pass

        # Try alternative strategies
        strategies = [
            self._try_id_variations,
            self._try_text_similarity,
            self._try_xpath_relative,
            self._try_ai_detection
        ]

        for strategy in strategies:
            if selector := await strategy(page, original_selector):
                self.locator_history[original_selector] = selector
                return selector

        return None

    async def _try_text_similarity(self, page: Page, original: str) -> Optional[str]:
        """Find elements with similar text content"""
        all_texts = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('*'))
                .map(el => el.textContent);
        }""")
        
        best_match = difflib.get_close_matches(original, all_texts, n=1, cutoff=0.8)
        if best_match:
            return f"text={best_match[0]}"
        return None

class TestHealer:
    def __init__(self):
        self.smart_locator = SmartLocator()
        self.healing_stats: Dict[str, int] = {"healed": 0, "failed": 0}

    async def heal_test(self, page: Page, test_case: dict) -> dict:
        """
        Attempt to heal a failing test by updating selectors and steps.
        """
        healed_steps = []
        for step in test_case["steps"]:
            if selector := self._extract_selector(step):
                new_selector = await self.smart_locator.find_element(page, selector)
                if new_selector:
                    step = step.replace(selector, new_selector)
                    self.healing_stats["healed"] += 1
                else:
                    self.healing_stats["failed"] += 1
            healed_steps.append(step)
        
        return {**test_case, "steps": healed_steps}

    def _extract_selector(self, step: str) -> Optional[str]:
        """Extract selector from test step"""
        selector_patterns = [
            r'click\s+"([^"]+)"',
            r'type\s+"([^"]+)"',
            r'select\s+"([^"]+)"'
        ]
        for pattern in selector_patterns:
            if match := re.search(pattern, step):
                return match.group(1)
        return None
```

### Integration in `src/agent/tools.py`:
```python
@tool
async def execute_playwright_test(test_case_json: str) -> str:
    """
    Enhanced test execution with self-healing capabilities.
    """
    test_case = json.loads(test_case_json)
    healer = TestHealer()
    
    try:
        # First try normal execution
        result = await run_test(test_case)
        if "PASS" in result:
            return result
            
        # If failed, attempt to heal
        healed_test = await healer.heal_test(page, test_case)
        result = await run_test(healed_test)
        
        if "PASS" in result:
            return f"PASS (Healed): {healer.healing_stats}"
        return f"FAIL: Test failed even after healing attempt"
    except Exception as e:
        return f"FAIL: {str(e)}"
```

## 2. Human Review Interface

### New Module `src/review/interface.py`:
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json

class TestReview(BaseModel):
    test_id: str
    approved: bool
    feedback: Optional[str]
    suggested_changes: Optional[dict]

class ReviewQueue:
    def __init__(self):
        self.pending_reviews: Dict[str, dict] = {}
        self.reviewed_tests: Dict[str, TestReview] = {}
        
    async def queue_for_review(self, test_case: dict) -> str:
        """Queue a test case for human review"""
        test_id = test_case["id"]
        self.pending_reviews[test_id] = test_case
        return test_id
        
    async def get_pending_reviews(self) -> List[dict]:
        """Get all tests waiting for review"""
        return list(self.pending_reviews.values())
        
    async def submit_review(self, review: TestReview) -> dict:
        """Process a human review submission"""
        if review.test_id not in self.pending_reviews:
            raise HTTPException(status_code=404, detail="Test not found")
            
        test_case = self.pending_reviews.pop(review.test_id)
        self.reviewed_tests[review.test_id] = review
        
        if review.suggested_changes:
            test_case.update(review.suggested_changes)
            
        return test_case
```

### Integration in `src/main.py`:
```python
from .review.interface import ReviewQueue, TestReview

review_queue = ReviewQueue()

@app.post("/review/queue-test")
async def queue_test_for_review(test_case: dict) -> dict:
    """Queue a test case for human review"""
    test_id = await review_queue.queue_for_review(test_case)
    return {"test_id": test_id, "status": "queued"}

@app.get("/review/pending")
async def get_pending_reviews() -> List[dict]:
    """Get all tests waiting for review"""
    return await review_queue.get_pending_reviews()

@app.post("/review/submit")
async def submit_review(review: TestReview) -> dict:
    """Submit a review for a test case"""
    updated_test = await review_queue.submit_review(review)
    return {"status": "approved" if review.approved else "rejected", "test": updated_test}
```

## 3. Enhanced Security Controls

### New Module `src/security/vector_store.py`:
```python
from cryptography.fernet import Fernet
from typing import List, Dict
import os
import json

class SecureVectorStore:
    def __init__(self):
        self.key = os.getenv("ENCRYPTION_KEY") or Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        
    def encrypt_document(self, document: dict) -> bytes:
        """Encrypt a document before storage"""
        doc_bytes = json.dumps(document).encode()
        return self.cipher_suite.encrypt(doc_bytes)
        
    def decrypt_document(self, encrypted_doc: bytes) -> dict:
        """Decrypt a stored document"""
        doc_bytes = self.cipher_suite.decrypt(encrypted_doc)
        return json.loads(doc_bytes)
        
    async def secure_ingest(self, documents: List[dict]) -> None:
        """Securely ingest documents into vector store"""
        encrypted_docs = [self.encrypt_document(doc) for doc in documents]
        # Store encrypted documents in Qdrant
        # Implementation depends on Qdrant's encryption support
```

### Integration in `src/rag/ingestion.py`:
```python
from ..security.vector_store import SecureVectorStore

secure_store = SecureVectorStore()

async def ingest_data():
    """Enhanced secure data ingestion"""
    loader = TextLoader("./data/jira_exports/sample_defects.txt")
    documents = loader.load()
    
    # Encrypt sensitive data
    await secure_store.secure_ingest(documents)
    
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    
    embeddings = OpenAIEmbeddings()
    
    # Store with encryption at rest
    Qdrant.from_documents(
        docs,
        embeddings,
        url=os.getenv("QDRANT_URL"),
        prefer_grpc=True,
        collection_name="historical_defects",
        encryption_key=secure_store.key
    )
```

## 4. Multi-Browser Support

### Enhancement to `playwright.yml`:
```yaml
- name: Install Playwright Browsers
  run: |
    playwright install --with-deps chromium firefox webkit
    playwright install-deps

- name: Run Tests Across Browsers
  env:
    BROWSERS: '["chromium", "firefox", "webkit"]'
  run: |
    for browser in $(echo $BROWSERS | jq -r '.[]'); do
      echo "Running tests in $browser..."
      python run_agent.py --browser $browser
    done
```

## 5. Feedback Collection System

### New Module `src/feedback/collector.py`:
```python
from typing import Dict, List
import datetime

class FeedbackCollector:
    def __init__(self):
        self.feedback_store: Dict[str, List[dict]] = {}
        
    async def collect_feedback(
        self,
        test_id: str,
        feedback_type: str,
        rating: int,
        comments: str
    ) -> dict:
        """Collect and store feedback for model improvement"""
        feedback = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": feedback_type,
            "rating": rating,
            "comments": comments
        }
        
        if test_id not in self.feedback_store:
            self.feedback_store[test_id] = []
            
        self.feedback_store[test_id].append(feedback)
        return feedback
        
    async def analyze_feedback(self) -> dict:
        """Analyze collected feedback for insights"""
        total_feedback = sum(len(f) for f in self.feedback_store.values())
        avg_rating = sum(
            f["rating"] for feedbacks in self.feedback_store.values()
            for f in feedbacks
        ) / total_feedback if total_feedback > 0 else 0
        
        return {
            "total_feedback": total_feedback,
            "average_rating": avg_rating,
            "feedback_by_type": self._group_by_type()
        }
        
    def _group_by_type(self) -> Dict[str, int]:
        """Group feedback by type"""
        type_counts = {}
        for feedbacks in self.feedback_store.values():
            for f in feedbacks:
                type_counts[f["type"]] = type_counts.get(f["type"], 0) + 1
        return type_counts
```

## Implementation Timeline

1. Phase 1 (Weeks 1-2):
   - Implement self-healing test framework
   - Add basic review interface
   - Set up secure vector store

2. Phase 2 (Weeks 3-4):
   - Expand browser support
   - Implement feedback system
   - Enhance security controls

3. Phase 3 (Weeks 5-6):
   - Add advanced reporting
   - Create dashboard UI
   - Implement continuous learning

## Success Metrics

1. Test Maintenance:
   - 50% reduction in test maintenance time
   - 80% success rate in self-healing attempts

2. Quality Metrics:
   - 95% test coverage of user stories
   - < 5% false positive rate in test results

3. Efficiency Gains:
   - 70% reduction in manual test creation time
   - 24-hour maximum turnaround for test review

## Next Steps

1. Immediate Actions:
   - Set up development environment for new modules
   - Create test data for self-healing mechanism
   - Design review interface mockups

2. Technical Prerequisites:
   - Update dependencies in requirements.txt
   - Set up secure key management
   - Configure multi-browser testing environment

3. Team Requirements:
   - Train QA team on review interface
   - Document self-healing mechanism
   - Establish feedback collection process
