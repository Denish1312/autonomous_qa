"""
Advanced test prioritization system for optimizing test execution order.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel
import numpy as np
from ..rag.analysis import RiskAnalyzer
from ..reporting.metrics import QualityMetrics

class TestPriority(BaseModel):
    """Priority score and factors for a test case"""
    test_id: str
    priority_score: float
    risk_score: float
    impact_score: float
    execution_time: float
    failure_probability: float
    last_execution: Optional[datetime]
    dependencies: List[str]

class TestDependency(BaseModel):
    """Dependency relationship between tests"""
    source_test: str
    target_test: str
    dependency_type: str  # setup, teardown, data, functional
    blocking: bool  # whether failure blocks dependent tests

class PrioritizationConfig(BaseModel):
    """Configuration for test prioritization"""
    risk_weight: float = 0.3
    impact_weight: float = 0.2
    time_weight: float = 0.15
    failure_weight: float = 0.2
    coverage_weight: float = 0.15
    max_batch_size: int = 10
    time_threshold: float = 3600  # 1 hour in seconds
    min_priority_for_execution: float = 0.3

class TestPrioritizer:
    def __init__(
        self,
        config: Optional[PrioritizationConfig] = None
    ):
        self.config = config or PrioritizationConfig()
        self.risk_analyzer = RiskAnalyzer()
        self.quality_metrics = QualityMetrics()
    
    async def prioritize_tests(
        self,
        test_suite: List[Dict],
        execution_history: Optional[List[Dict]] = None,
        dependencies: Optional[List[TestDependency]] = None
    ) -> List[Dict]:
        """
        Prioritize tests based on multiple factors including risk, impact,
        execution time, and dependencies.
        
        Args:
            test_suite: List of test cases to prioritize
            execution_history: Optional historical execution data
            dependencies: Optional test dependencies
        
        Returns:
            Prioritized list of test cases
        """
        # Calculate priority scores
        priority_scores = await self._calculate_priority_scores(
            test_suite,
            execution_history
        )
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(
            test_suite,
            dependencies
        )
        
        # Create execution batches considering dependencies
        prioritized_tests = await self._create_execution_batches(
            test_suite,
            priority_scores,
            dependency_graph
        )
        
        return prioritized_tests
    
    async def _calculate_priority_scores(
        self,
        test_suite: List[Dict],
        execution_history: Optional[List[Dict]]
    ) -> Dict[str, TestPriority]:
        """Calculate priority scores for each test"""
        priority_scores = {}
        
        for test in test_suite:
            # Get risk score
            risk_score = await self._calculate_risk_score(test)
            
            # Get impact score
            impact_score = await self._calculate_impact_score(test)
            
            # Get execution metrics
            execution_metrics = await self._get_execution_metrics(
                test,
                execution_history
            )
            
            # Calculate failure probability
            failure_prob = await self._calculate_failure_probability(
                test,
                execution_history
            )
            
            # Calculate overall priority score
            priority_score = (
                self.config.risk_weight * risk_score +
                self.config.impact_weight * impact_score +
                self.config.time_weight * (1 - execution_metrics["normalized_time"]) +
                self.config.failure_weight * failure_prob +
                self.config.coverage_weight * execution_metrics["coverage_score"]
            )
            
            priority_scores[test["id"]] = TestPriority(
                test_id=test["id"],
                priority_score=priority_score,
                risk_score=risk_score,
                impact_score=impact_score,
                execution_time=execution_metrics["execution_time"],
                failure_probability=failure_prob,
                last_execution=execution_metrics["last_execution"],
                dependencies=[]
            )
        
        return priority_scores
    
    async def _calculate_risk_score(self, test: Dict) -> float:
        """Calculate risk score for a test"""
        try:
            risk_analysis = await self.risk_analyzer.calculate_risk_score(
                test.get("feature", "")
            )
            return risk_analysis.overall_score
        except:
            return 0.5  # Default medium risk
    
    async def _calculate_impact_score(self, test: Dict) -> float:
        """Calculate business impact score for a test"""
        impact_levels = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2
        }
        return impact_levels.get(test.get("impact", "medium"), 0.5)
    
    async def _get_execution_metrics(
        self,
        test: Dict,
        execution_history: Optional[List[Dict]]
    ) -> Dict:
        """Get execution metrics for a test"""
        if not execution_history:
            return {
                "execution_time": 300,  # Default 5 minutes
                "normalized_time": 0.5,
                "coverage_score": 0.5,
                "last_execution": None
            }
        
        # Filter history for this test
        test_history = [
            h for h in execution_history
            if h["test_id"] == test["id"]
        ]
        
        if not test_history:
            return {
                "execution_time": 300,
                "normalized_time": 0.5,
                "coverage_score": 0.5,
                "last_execution": None
            }
        
        # Calculate average execution time
        execution_times = [h["duration"] for h in test_history if "duration" in h]
        avg_time = np.mean(execution_times) if execution_times else 300
        
        # Normalize execution time (0-1 scale)
        normalized_time = min(avg_time / self.config.time_threshold, 1.0)
        
        # Calculate coverage score
        coverage = sum(1 for h in test_history if h.get("coverage")) / len(test_history)
        
        # Get last execution time
        last_execution = max(
            (h["timestamp"] for h in test_history if "timestamp" in h),
            default=None
        )
        
        return {
            "execution_time": avg_time,
            "normalized_time": normalized_time,
            "coverage_score": coverage,
            "last_execution": last_execution
        }
    
    async def _calculate_failure_probability(
        self,
        test: Dict,
        execution_history: Optional[List[Dict]]
    ) -> float:
        """Calculate probability of test failure"""
        if not execution_history:
            return 0.5  # Default medium probability
        
        # Filter history for this test
        test_history = [
            h for h in execution_history
            if h["test_id"] == test["id"]
        ]
        
        if not test_history:
            return 0.5
        
        # Calculate failure rate
        failures = sum(1 for h in test_history if h["status"] == "failed")
        failure_rate = failures / len(test_history)
        
        # Apply time decay to give more weight to recent failures
        weighted_failure_rate = 0
        total_weight = 0
        
        for history in sorted(test_history, key=lambda h: h["timestamp"]):
            age_days = (datetime.now() - history["timestamp"]).days
            weight = 1 / (1 + age_days/30)  # Decay over 30 days
            weighted_failure_rate += weight * (1 if history["status"] == "failed" else 0)
            total_weight += weight
        
        if total_weight > 0:
            weighted_failure_rate /= total_weight
        
        # Combine recent and overall failure rates
        return 0.7 * weighted_failure_rate + 0.3 * failure_rate
    
    def _build_dependency_graph(
        self,
        test_suite: List[Dict],
        dependencies: Optional[List[TestDependency]]
    ) -> Dict[str, List[str]]:
        """Build graph of test dependencies"""
        graph = {test["id"]: [] for test in test_suite}
        
        if not dependencies:
            return graph
        
        # Add dependencies to graph
        for dep in dependencies:
            if dep.blocking:
                graph[dep.source_test].append(dep.target_test)
        
        return graph
    
    async def _create_execution_batches(
        self,
        test_suite: List[Dict],
        priority_scores: Dict[str, TestPriority],
        dependency_graph: Dict[str, List[str]]
    ) -> List[Dict]:
        """Create execution batches considering priorities and dependencies"""
        # Sort tests by priority score
        sorted_tests = sorted(
            test_suite,
            key=lambda t: priority_scores[t["id"]].priority_score,
            reverse=True
        )
        
        # Initialize result list and tracking sets
        prioritized = []
        executed = set()
        blocked = set()
        
        while sorted_tests:
            # Create next batch
            batch = []
            batch_time = 0
            
            # Add tests to batch
            for test in sorted_tests[:]:
                test_id = test["id"]
                test_time = priority_scores[test_id].execution_time
                
                # Skip if test is blocked or exceeds batch limits
                if (
                    test_id in blocked or
                    len(batch) >= self.config.max_batch_size or
                    batch_time + test_time > self.config.time_threshold or
                    priority_scores[test_id].priority_score < self.config.min_priority_for_execution
                ):
                    continue
                
                # Check if all dependencies are satisfied
                dependencies = dependency_graph[test_id]
                if all(dep in executed for dep in dependencies):
                    batch.append(test)
                    batch_time += test_time
                    executed.add(test_id)
                    sorted_tests.remove(test)
                else:
                    blocked.add(test_id)
            
            # Add batch to result if not empty
            if batch:
                prioritized.extend(batch)
            else:
                # If no tests could be added, there might be a dependency cycle
                # Add the highest priority non-executed test
                for test in sorted_tests:
                    if test["id"] not in executed:
                        prioritized.append(test)
                        executed.add(test["id"])
                        sorted_tests.remove(test)
                        break
        
        return prioritized
