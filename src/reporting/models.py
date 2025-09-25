"""
Models for the test reporting system.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import uuid

class TestStatus(str, Enum):
    """Test execution status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    HEALED = "healed"  # Test passed after self-healing

class TestSeverity(str, Enum):
    """Test failure severity"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TestCategory(str, Enum):
    """Test categories"""
    FUNCTIONAL = "functional"
    REGRESSION = "regression"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"

class TestArtifact(BaseModel):
    """Model for test artifacts (screenshots, logs, etc.)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # screenshot, log, trace, video
    path: str
    content_type: str
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class TestStep(BaseModel):
    """Model for individual test steps"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    status: TestStatus
    duration_ms: int
    artifacts: List[TestArtifact] = []
    error_message: Optional[str] = None
    healing_attempts: Optional[int] = None
    healing_successful: Optional[bool] = None

class TestCase(BaseModel):
    """Model for test case execution results"""
    id: str
    title: str
    description: Optional[str] = None
    category: TestCategory
    severity: TestSeverity = TestSeverity.MEDIUM
    status: TestStatus
    duration_ms: int
    steps: List[TestStep]
    artifacts: List[TestArtifact] = []
    error_message: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    started_at: datetime
    completed_at: datetime

class TestSuite(BaseModel):
    """Model for test suite execution results"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    test_cases: List[TestCase]
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    healed_tests: int
    total_duration_ms: int
    started_at: datetime
    completed_at: datetime
    environment: Dict[str, str] = {}
    metadata: Dict[str, Any] = {}

class TestTrend(BaseModel):
    """Model for historical test trends"""
    date: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    healed_tests: int
    avg_duration_ms: int
    failure_rate: float
    healing_success_rate: float

class TestReport(BaseModel):
    """Model for comprehensive test report"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    test_suites: List[TestSuite]
    summary: Dict[str, Any]
    trends: List[TestTrend]
    generated_at: datetime = Field(default_factory=datetime.now)
    version: str
    environment: Dict[str, str]
    metadata: Dict[str, Any] = {}
