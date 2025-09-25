"""
Enhanced quality metrics system with comprehensive coverage, performance, and reliability metrics.
"""

from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel
import numpy as np
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class CodeCoverage:
    """Detailed code coverage metrics"""
    line_coverage: float
    branch_coverage: float
    function_coverage: float
    statement_coverage: float
    uncovered_lines: List[str]
    critical_paths_coverage: float
    modified_lines_coverage: float

class FeatureCoverage(BaseModel):
    """Feature-level coverage metrics"""
    feature_name: str
    test_cases: int
    scenarios_covered: int
    total_scenarios: int
    coverage_percentage: float
    missing_scenarios: List[str]
    risk_areas: List[str]

class PerformanceMetrics(BaseModel):
    """Detailed test performance metrics"""
    avg_response_time: float
    p90_response_time: float
    p95_response_time: float
    p99_response_time: float
    max_response_time: float
    min_response_time: float
    std_deviation: float
    throughput: float

class ReliabilityMetrics(BaseModel):
    """Enhanced reliability metrics"""
    stability_score: float
    flakiness_rate: float
    recovery_rate: float
    mtbf: float  # Mean Time Between Failures
    mttr: float  # Mean Time To Recovery
    error_clustering: Dict[str, int]
    failure_patterns: List[str]

class TrendMetrics(BaseModel):
    """Trend analysis metrics"""
    date: datetime
    coverage_trend: float
    reliability_trend: float
    performance_trend: float
    defect_density_trend: float
    maintenance_effort_trend: float

class EnhancedQualityMetrics:
    """Enhanced quality metrics analyzer"""
    
    def __init__(self):
        self.coverage_thresholds = {
            "critical": 0.95,
            "high": 0.90,
            "medium": 0.80,
            "low": 0.70
        }
    
    async def analyze_code_coverage(
        self,
        coverage_data: Dict[str, Any],
        critical_paths: List[str],
        modified_files: List[str]
    ) -> CodeCoverage:
        """
        Analyze detailed code coverage metrics.
        
        Args:
            coverage_data: Raw coverage data
            critical_paths: List of critical code paths
            modified_files: Recently modified files
        """
        # Calculate basic coverage metrics
        line_coverage = self._calculate_line_coverage(coverage_data)
        branch_coverage = self._calculate_branch_coverage(coverage_data)
        function_coverage = self._calculate_function_coverage(coverage_data)
        statement_coverage = self._calculate_statement_coverage(coverage_data)
        
        # Find uncovered lines
        uncovered_lines = self._find_uncovered_lines(coverage_data)
        
        # Calculate critical path coverage
        critical_paths_coverage = self._calculate_critical_path_coverage(
            coverage_data,
            critical_paths
        )
        
        # Calculate modified lines coverage
        modified_lines_coverage = self._calculate_modified_lines_coverage(
            coverage_data,
            modified_files
        )
        
        return CodeCoverage(
            line_coverage=line_coverage,
            branch_coverage=branch_coverage,
            function_coverage=function_coverage,
            statement_coverage=statement_coverage,
            uncovered_lines=uncovered_lines,
            critical_paths_coverage=critical_paths_coverage,
            modified_lines_coverage=modified_lines_coverage
        )
    
    async def analyze_feature_coverage(
        self,
        test_cases: List[Dict],
        feature_requirements: Dict[str, List[str]]
    ) -> List[FeatureCoverage]:
        """
        Analyze feature-level test coverage.
        
        Args:
            test_cases: List of test cases
            feature_requirements: Dictionary of features and their requirements
        """
        feature_coverage = []
        
        for feature, requirements in feature_requirements.items():
            # Count test cases for feature
            feature_tests = [
                tc for tc in test_cases
                if tc.get("feature") == feature
            ]
            
            # Analyze scenarios covered
            covered_scenarios = set()
            for test in feature_tests:
                covered_scenarios.update(test.get("scenarios", []))
            
            # Calculate coverage
            total_scenarios = set(requirements)
            missing = total_scenarios - covered_scenarios
            coverage_pct = len(covered_scenarios) / len(total_scenarios) * 100
            
            # Identify risk areas
            risk_areas = self._identify_risk_areas(
                feature,
                missing,
                test_cases
            )
            
            feature_coverage.append(FeatureCoverage(
                feature_name=feature,
                test_cases=len(feature_tests),
                scenarios_covered=len(covered_scenarios),
                total_scenarios=len(total_scenarios),
                coverage_percentage=coverage_pct,
                missing_scenarios=list(missing),
                risk_areas=risk_areas
            ))
        
        return feature_coverage
    
    async def analyze_performance(
        self,
        execution_times: List[float],
        resource_usage: List[Dict]
    ) -> PerformanceMetrics:
        """
        Analyze test execution performance metrics.
        
        Args:
            execution_times: List of test execution times
            resource_usage: Resource usage data during test execution
        """
        if not execution_times:
            return PerformanceMetrics(
                avg_response_time=0,
                p90_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                max_response_time=0,
                min_response_time=0,
                std_deviation=0,
                throughput=0
            )
        
        # Calculate basic statistics
        avg_time = np.mean(execution_times)
        std_dev = np.std(execution_times)
        
        # Calculate percentiles
        p90 = np.percentile(execution_times, 90)
        p95 = np.percentile(execution_times, 95)
        p99 = np.percentile(execution_times, 99)
        
        # Calculate throughput (tests per second)
        total_time = sum(execution_times)
        throughput = len(execution_times) / total_time if total_time > 0 else 0
        
        return PerformanceMetrics(
            avg_response_time=avg_time,
            p90_response_time=p90,
            p95_response_time=p95,
            p99_response_time=p99,
            max_response_time=max(execution_times),
            min_response_time=min(execution_times),
            std_deviation=std_dev,
            throughput=throughput
        )
    
    async def analyze_reliability(
        self,
        test_results: List[Dict],
        error_logs: List[Dict]
    ) -> ReliabilityMetrics:
        """
        Analyze test reliability and stability metrics.
        
        Args:
            test_results: Historical test execution results
            error_logs: Error and failure logs
        """
        # Calculate stability score
        stability_score = self._calculate_stability_score(test_results)
        
        # Calculate flakiness rate
        flakiness_rate = self._calculate_flakiness_rate(test_results)
        
        # Calculate recovery metrics
        recovery_metrics = self._calculate_recovery_metrics(test_results)
        
        # Analyze error patterns
        error_patterns = self._analyze_error_patterns(error_logs)
        
        return ReliabilityMetrics(
            stability_score=stability_score,
            flakiness_rate=flakiness_rate,
            recovery_rate=recovery_metrics["recovery_rate"],
            mtbf=recovery_metrics["mtbf"],
            mttr=recovery_metrics["mttr"],
            error_clustering=error_patterns["clusters"],
            failure_patterns=error_patterns["patterns"]
        )
    
    async def analyze_trends(
        self,
        historical_data: List[Dict],
        window_size: int = 30
    ) -> List[TrendMetrics]:
        """
        Analyze trends in quality metrics over time.
        
        Args:
            historical_data: Historical metrics data
            window_size: Window size for trend analysis in days
        """
        trends = []
        
        # Group data by date
        daily_metrics = self._group_by_date(historical_data)
        
        # Calculate moving averages
        for date, metrics in sorted(daily_metrics.items()):
            coverage_trend = self._calculate_moving_average(
                metrics["coverage"],
                window_size
            )
            reliability_trend = self._calculate_moving_average(
                metrics["reliability"],
                window_size
            )
            performance_trend = self._calculate_moving_average(
                metrics["performance"],
                window_size
            )
            defect_trend = self._calculate_moving_average(
                metrics["defect_density"],
                window_size
            )
            maintenance_trend = self._calculate_moving_average(
                metrics["maintenance_effort"],
                window_size
            )
            
            trends.append(TrendMetrics(
                date=date,
                coverage_trend=coverage_trend,
                reliability_trend=reliability_trend,
                performance_trend=performance_trend,
                defect_density_trend=defect_trend,
                maintenance_effort_trend=maintenance_trend
            ))
        
        return trends
    
    def _calculate_line_coverage(self, coverage_data: Dict) -> float:
        """Calculate line coverage percentage"""
        total_lines = coverage_data.get("total_lines", 0)
        covered_lines = coverage_data.get("covered_lines", 0)
        return (covered_lines / total_lines * 100) if total_lines > 0 else 0
    
    def _calculate_branch_coverage(self, coverage_data: Dict) -> float:
        """Calculate branch coverage percentage"""
        total_branches = coverage_data.get("total_branches", 0)
        covered_branches = coverage_data.get("covered_branches", 0)
        return (covered_branches / total_branches * 100) if total_branches > 0 else 0
    
    def _calculate_function_coverage(self, coverage_data: Dict) -> float:
        """Calculate function coverage percentage"""
        total_functions = coverage_data.get("total_functions", 0)
        covered_functions = coverage_data.get("covered_functions", 0)
        return (covered_functions / total_functions * 100) if total_functions > 0 else 0
    
    def _calculate_statement_coverage(self, coverage_data: Dict) -> float:
        """Calculate statement coverage percentage"""
        total_statements = coverage_data.get("total_statements", 0)
        covered_statements = coverage_data.get("covered_statements", 0)
        return (covered_statements / total_statements * 100) if total_statements > 0 else 0
    
    def _find_uncovered_lines(self, coverage_data: Dict) -> List[str]:
        """Find lines without test coverage"""
        uncovered = []
        for file, data in coverage_data.get("files", {}).items():
            for line, covered in data.get("lines", {}).items():
                if not covered:
                    uncovered.append(f"{file}:{line}")
        return uncovered
    
    def _calculate_critical_path_coverage(
        self,
        coverage_data: Dict,
        critical_paths: List[str]
    ) -> float:
        """Calculate coverage for critical code paths"""
        if not critical_paths:
            return 100.0
            
        covered_paths = 0
        for path in critical_paths:
            if self._is_path_covered(path, coverage_data):
                covered_paths += 1
                
        return (covered_paths / len(critical_paths) * 100)
    
    def _calculate_modified_lines_coverage(
        self,
        coverage_data: Dict,
        modified_files: List[str]
    ) -> float:
        """Calculate coverage for recently modified lines"""
        if not modified_files:
            return 100.0
            
        total_modified = 0
        covered_modified = 0
        
        for file in modified_files:
            file_data = coverage_data.get("files", {}).get(file, {})
            modified_lines = file_data.get("modified_lines", [])
            total_modified += len(modified_lines)
            covered_modified += sum(
                1 for line in modified_lines
                if file_data.get("lines", {}).get(str(line), False)
            )
        
        return (covered_modified / total_modified * 100) if total_modified > 0 else 100.0
    
    def _identify_risk_areas(
        self,
        feature: str,
        missing_scenarios: Set[str],
        test_cases: List[Dict]
    ) -> List[str]:
        """Identify potential risk areas in feature coverage"""
        risk_areas = []
        
        # Check critical scenario coverage
        critical_scenarios = {
            s for s in missing_scenarios
            if "critical" in s.lower() or "high" in s.lower()
        }
        if critical_scenarios:
            risk_areas.append(f"Missing critical scenarios: {len(critical_scenarios)}")
        
        # Check edge case coverage
        edge_cases = {
            s for s in missing_scenarios
            if "edge" in s.lower() or "boundary" in s.lower()
        }
        if edge_cases:
            risk_areas.append(f"Missing edge cases: {len(edge_cases)}")
        
        # Check negative test coverage
        negative_tests = sum(
            1 for tc in test_cases
            if tc.get("feature") == feature and tc.get("type") == "negative"
        )
        if negative_tests < len(test_cases) * 0.2:  # Expect at least 20% negative tests
            risk_areas.append("Insufficient negative test coverage")
        
        return risk_areas
    
    def _calculate_stability_score(self, test_results: List[Dict]) -> float:
        """Calculate test stability score"""
        if not test_results:
            return 1.0
            
        # Count consistent passes/fails
        consistent_results = defaultdict(list)
        for result in test_results:
            test_id = result["test_id"]
            consistent_results[test_id].append(result["status"])
        
        stable_tests = sum(
            1 for results in consistent_results.values()
            if len(set(results)) == 1  # All results same status
        )
        
        return stable_tests / len(consistent_results)
    
    def _calculate_flakiness_rate(self, test_results: List[Dict]) -> float:
        """Calculate test flakiness rate"""
        if not test_results:
            return 0.0
            
        # Group by test ID
        test_runs = defaultdict(list)
        for result in test_results:
            test_runs[result["test_id"]].append(result["status"])
        
        # Count flaky tests (tests with inconsistent results)
        flaky_tests = sum(
            1 for results in test_runs.values()
            if len(set(results)) > 1  # Multiple different statuses
        )
        
        return flaky_tests / len(test_runs)
    
    def _calculate_recovery_metrics(
        self,
        test_results: List[Dict]
    ) -> Dict[str, float]:
        """Calculate test recovery metrics"""
        if not test_results:
            return {
                "recovery_rate": 1.0,
                "mtbf": float("inf"),
                "mttr": 0.0
            }
        
        # Calculate recovery rate
        failure_sequences = defaultdict(list)
        for result in sorted(test_results, key=lambda x: x["timestamp"]):
            test_id = result["test_id"]
            failure_sequences[test_id].append(result["status"])
        
        recoveries = 0
        failures = 0
        repair_times = []
        between_failures = []
        
        for test_id, sequence in failure_sequences.items():
            last_status = None
            last_failure = None
            last_success = None
            
            for i, status in enumerate(sequence):
                if status == "failed":
                    failures += 1
                    if last_status == "passed":
                        if last_success is not None:
                            between_failures.append(i - last_success)
                    last_failure = i
                elif status == "passed":
                    if last_status == "failed":
                        recoveries += 1
                        if last_failure is not None:
                            repair_times.append(i - last_failure)
                    last_success = i
                last_status = status
        
        recovery_rate = recoveries / failures if failures > 0 else 1.0
        mttr = np.mean(repair_times) if repair_times else 0.0
        mtbf = np.mean(between_failures) if between_failures else float("inf")
        
        return {
            "recovery_rate": recovery_rate,
            "mtbf": mtbf,
            "mttr": mttr
        }
    
    def _analyze_error_patterns(self, error_logs: List[Dict]) -> Dict:
        """Analyze error patterns and clusters"""
        if not error_logs:
            return {"clusters": {}, "patterns": []}
        
        # Group errors by type
        error_clusters = defaultdict(int)
        for log in error_logs:
            error_type = log.get("error_type", "unknown")
            error_clusters[error_type] += 1
        
        # Identify common patterns
        patterns = []
        for error_type, count in sorted(
            error_clusters.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if count > len(error_logs) * 0.1:  # More than 10% of errors
                patterns.append(
                    f"Frequent error pattern: {error_type} ({count} occurrences)"
                )
        
        return {
            "clusters": dict(error_clusters),
            "patterns": patterns
        }
    
    def _group_by_date(self, historical_data: List[Dict]) -> Dict:
        """Group metrics data by date"""
        daily_metrics = defaultdict(lambda: defaultdict(list))
        
        for entry in historical_data:
            date = entry["timestamp"].date()
            for metric_type in [
                "coverage",
                "reliability",
                "performance",
                "defect_density",
                "maintenance_effort"
            ]:
                if metric_type in entry:
                    daily_metrics[date][metric_type].append(entry[metric_type])
        
        return daily_metrics
    
    def _calculate_moving_average(
        self,
        values: List[float],
        window_size: int
    ) -> float:
        """Calculate moving average for trend analysis"""
        if not values:
            return 0.0
            
        window = values[-window_size:] if len(values) > window_size else values
        return np.mean(window)
