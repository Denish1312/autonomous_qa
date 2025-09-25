from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict

class TestStep(BaseModel):
    """A single step in a test sequence"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    action: str
    params: Dict[str, Any]
    expected_result: Optional[str] = None

class TestPlan(BaseModel):
    """A complete test plan"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    steps: List[TestStep]
    context: Dict[str, Any]

class TestResult(BaseModel):
    """Result of a test execution"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    artifacts: Optional[List[str]] = None

class BaseAgent(ABC):
    """Base class for autonomous testing agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.context = {}
    
    @abstractmethod
    async def plan(self, url: str, test_type: str) -> TestPlan:
        """Generate a test plan for the given URL and test type"""
        pass
    
    @abstractmethod
    async def execute(self, plan: TestPlan) -> TestResult:
        """Execute a test plan and return results"""
        pass
    
    @abstractmethod
    async def analyze(self, result: TestResult) -> Dict[str, Any]:
        """Analyze test results and provide insights"""
        pass

class MockAgent(BaseAgent):
    """A mock agent for testing the infrastructure"""
    
    async def plan(self, url: str, test_type: str) -> TestPlan:
        return TestPlan(
            steps=[
                TestStep(
                    action="navigate",
                    params={"url": url},
                    expected_result="Page loads successfully"
                ),
                TestStep(
                    action="check_title",
                    params={},
                    expected_result="Page has a non-empty title"
                )
            ],
            context={"test_type": test_type}
        )
    
    async def execute(self, plan: TestPlan) -> TestResult:
        return TestResult(
            success=True,
            message="Mock test executed successfully",
            details={"steps_completed": len(plan.steps)},
            artifacts=["test_screenshot.png"]
        )
    
    async def analyze(self, result: TestResult) -> Dict[str, Any]:
        return {
            "summary": "All tests passed",
            "confidence": 1.0,
            "recommendations": ["No issues found"]
        }