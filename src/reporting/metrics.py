"""
Enhanced quality metrics system for measuring test automation effectiveness.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel
import numpy as np
from ..rag.analysis import RiskAnalyzer

class TestExecutionMetrics(BaseModel):
    """Metrics for test execution"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    flaky_tests: int
    skipped_tests: int
    execution_time: float  # in seconds
    average_duration: float  # in seconds
    parallel_efficiency: float  # percentage

class AutomationMetrics(BaseModel):
    """Metrics for automation effectiveness"""
    automation_coverage: float  # percentage
    maintenance_time: float  # hours per month
    creation_time: float  # hours per test
    execution_cost: float  # cost per run
    reliability: float  # percentage

class DefectMetrics(BaseModel):
    """Metrics for defect detection"""
    defects_found: int
    false_positives: int
    escaped_defects: int
    prevention_rate: float  # percentage
    detection_efficiency: float  # defects per test hour

class ROIMetrics(BaseModel):
    """Metrics for return on investment"""
    manual_cost: float  # cost of manual testing
    automation_cost: float  # cost of automated testing
    time_savings: float  # hours saved
    cost_savings: float  # money saved
    roi_percentage: float  # ROI as percentage

class QualityMetrics:
    def __init__(self):
        self.risk_analyzer = RiskAnalyzer()
    
    async def calculate_automation_roi(
        self,
        test_results: List[Dict],
        manual_metrics: Dict[str, float],
        automation_costs: Dict[str, float]
    ) -> ROIMetrics:
        """
        Calculate ROI of test automation.
        
        Args:
            test_results: Historical test execution results
            manual_metrics: Metrics from manual testing
            automation_costs: Costs associated with automation
        """
        # Calculate manual testing costs
        manual_cost = (
            manual_metrics["hourly_rate"] *
            manual_metrics["hours_per_cycle"] *
            manual_metrics["cycles_per_year"]
        )
        
        # Calculate automation costs
        setup_cost = automation_costs.get("setup", 0)
        maintenance_cost = automation_costs.get("maintenance_monthly", 0) * 12
        execution_cost = automation_costs.get("execution_per_run", 0) * len(test_results)
        total_automation_cost = setup_cost + maintenance_cost + execution_cost
        
        # Calculate time savings
        manual_time = manual_metrics["hours_per_cycle"] * manual_metrics["cycles_per_year"]
        automation_time = (
            automation_costs.get("maintenance_monthly", 0) * 12 +
            (automation_costs.get("execution_minutes", 0) * len(test_results)) / 60
        )
        time_savings = manual_time - automation_time
        
        # Calculate cost savings
        cost_savings = manual_cost - total_automation_cost
        
        # Calculate ROI percentage
        roi_percentage = (cost_savings / total_automation_cost * 100) if total_automation_cost > 0 else 0
        
        return ROIMetrics(
            manual_cost=manual_cost,
            automation_cost=total_automation_cost,
            time_savings=time_savings,
            cost_savings=cost_savings,
            roi_percentage=roi_percentage
        )
    
    async def calculate_execution_metrics(
        self,
        test_results: List[Dict],
        execution_history: List[Dict]
    ) -> TestExecutionMetrics:
        """Calculate metrics related to test execution"""
        total = len(test_results)
        if total == 0:
            return TestExecutionMetrics(
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                flaky_tests=0,
                skipped_tests=0,
                execution_time=0.0,
                average_duration=0.0,
                parallel_efficiency=0.0
            )
        
        # Count test results
        passed = sum(1 for t in test_results if t["status"] == "passed")
        failed = sum(1 for t in test_results if t["status"] == "failed")
        skipped = sum(1 for t in test_results if t["status"] == "skipped")
        
        # Calculate flaky tests
        flaky_tests = await self._identify_flaky_tests(execution_history)
        
        # Calculate timing metrics
        execution_times = [t["duration"] for t in test_results if "duration" in t]
        total_time = sum(execution_times)
        avg_duration = np.mean(execution_times) if execution_times else 0
        
        # Calculate parallel efficiency
        parallel_efficiency = await self._calculate_parallel_efficiency(execution_history)
        
        return TestExecutionMetrics(
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            flaky_tests=len(flaky_tests),
            skipped_tests=skipped,
            execution_time=total_time,
            average_duration=avg_duration,
            parallel_efficiency=parallel_efficiency
        )
    
    async def calculate_automation_metrics(
        self,
        test_results: List[Dict],
        manual_test_count: int,
        maintenance_logs: List[Dict]
    ) -> AutomationMetrics:
        """Calculate metrics related to automation effectiveness"""
        total_tests = len(test_results) + manual_test_count
        automated_tests = len(test_results)
        
        # Calculate automation coverage
        automation_coverage = (automated_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate maintenance metrics
        maintenance_hours = sum(log["duration_hours"] for log in maintenance_logs)
        avg_maintenance = maintenance_hours / 30  # per month
        
        # Calculate creation time
        creation_times = [t.get("creation_time", 0) for t in test_results]
        avg_creation_time = np.mean(creation_times) if creation_times else 0
        
        # Calculate execution cost
        total_duration = sum(t.get("duration", 0) for t in test_results)
        execution_cost = total_duration * 0.00028  # Assumed cloud cost per second
        
        # Calculate reliability
        reliability = await self._calculate_test_reliability(test_results)
        
        return AutomationMetrics(
            automation_coverage=automation_coverage,
            maintenance_time=avg_maintenance,
            creation_time=avg_creation_time,
            execution_cost=execution_cost,
            reliability=reliability
        )
    
    async def calculate_defect_metrics(
        self,
        test_results: List[Dict],
        production_defects: List[Dict]
    ) -> DefectMetrics:
        """Calculate metrics related to defect detection"""
        # Count defects found by tests
        defects_found = sum(1 for t in test_results if t.get("found_defect"))
        
        # Count false positives
        false_positives = sum(1 for t in test_results if t.get("false_positive"))
        
        # Count escaped defects (found in production)
        escaped_defects = len(production_defects)
        
        # Calculate prevention rate
        total_defects = defects_found + escaped_defects
        prevention_rate = (defects_found / total_defects * 100) if total_defects > 0 else 0
        
        # Calculate detection efficiency
        total_hours = sum(t.get("duration", 0) for t in test_results) / 3600
        detection_efficiency = defects_found / total_hours if total_hours > 0 else 0
        
        return DefectMetrics(
            defects_found=defects_found,
            false_positives=false_positives,
            escaped_defects=escaped_defects,
            prevention_rate=prevention_rate,
            detection_efficiency=detection_efficiency
        )
    
    async def _identify_flaky_tests(
        self,
        execution_history: List[Dict]
    ) -> List[str]:
        """Identify flaky tests from execution history"""
        flaky_tests = []
        test_results = {}
        
        # Group results by test ID
        for execution in execution_history:
            test_id = execution["test_id"]
            if test_id not in test_results:
                test_results[test_id] = []
            test_results[test_id].append(execution["status"])
        
        # Identify tests with inconsistent results
        for test_id, results in test_results.items():
            if len(results) >= 3:  # Require at least 3 executions
                if len(set(results)) > 1:  # More than one unique result
                    flaky_tests.append(test_id)
        
        return flaky_tests
    
    async def _calculate_parallel_efficiency(
        self,
        execution_history: List[Dict]
    ) -> float:
        """Calculate efficiency of parallel test execution"""
        if not execution_history:
            return 0.0
        
        # Group executions by run ID
        runs = {}
        for execution in execution_history:
            run_id = execution["run_id"]
            if run_id not in runs:
                runs[run_id] = []
            runs[run_id].append(execution)
        
        efficiencies = []
        for run_executions in runs.values():
            if not run_executions:
                continue
            
            # Calculate theoretical minimum time (sum of all test durations / number of parallel instances)
            total_duration = sum(e["duration"] for e in run_executions)
            actual_duration = max(e["end_time"] - e["start_time"] for e in run_executions)
            max_parallel = 4  # Assumed maximum parallel instances
            
            theoretical_minimum = total_duration / max_parallel
            efficiency = (theoretical_minimum / actual_duration * 100) if actual_duration > 0 else 0
            efficiencies.append(min(efficiency, 100))  # Cap at 100%
        
        return np.mean(efficiencies) if efficiencies else 0.0
    
    async def _calculate_test_reliability(
        self,
        test_results: List[Dict]
    ) -> float:
        """Calculate test reliability score"""
        if not test_results:
            return 0.0
        
        # Calculate success rate
        success_rate = sum(1 for t in test_results if t["status"] == "passed") / len(test_results)
        
        # Calculate stability (inverse of flakiness)
        flaky_tests = await self._identify_flaky_tests(test_results)
        stability = 1 - (len(flaky_tests) / len(test_results))
        
        # Calculate maintenance ratio
        maintenance_ratio = 1 - (
            sum(1 for t in test_results if t.get("needs_maintenance", False)) / len(test_results)
        )
        
        # Weighted combination
        weights = {
            "success_rate": 0.4,
            "stability": 0.4,
            "maintenance": 0.2
        }
        
        reliability = (
            weights["success_rate"] * success_rate +
            weights["stability"] * stability +
            weights["maintenance"] * maintenance_ratio
        ) * 100
        
        return reliability
