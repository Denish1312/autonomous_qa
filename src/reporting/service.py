"""
Service layer for test report generation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
import plotly.graph_objects as go
from jinja2 import Template
import markdown2
from .models import (
    TestReport, TestSuite, TestCase, TestTrend,
    TestStatus, TestArtifact
)
from .templates import HTML_TEMPLATE, MARKDOWN_TEMPLATE

class ReportingService:
    def __init__(self, storage_path: str = "./data/reports"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def _calculate_summary(self, test_suites: List[TestSuite]) -> Dict[str, Any]:
        """Calculate summary statistics from test suites"""
        total_tests = sum(suite.total_tests for suite in test_suites)
        passed_tests = sum(suite.passed_tests for suite in test_suites)
        healed_tests = sum(suite.healed_tests for suite in test_suites)
        total_duration = sum(suite.total_duration_ms for suite in test_suites)
        
        return {
            "total_tests": total_tests,
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "healing_rate": (healed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": self._format_duration(total_duration)
        }
    
    def _calculate_trends(self, days: int = 30) -> List[TestTrend]:
        """Calculate test execution trends from historical data"""
        trends = []
        start_date = datetime.now() - timedelta(days=days)
        
        # Load historical reports
        historical_reports = []
        for report_file in self.storage_path.glob("*.json"):
            if report_file.stat().st_mtime >= start_date.timestamp():
                with open(report_file, "r") as f:
                    historical_reports.append(TestReport(**json.load(f)))
        
        # Group by date
        daily_stats = {}
        for report in historical_reports:
            date = report.generated_at.date()
            if date not in daily_stats:
                daily_stats[date] = {
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "skipped_tests": 0,
                    "error_tests": 0,
                    "healed_tests": 0,
                    "total_duration": 0,
                    "count": 0
                }
            
            stats = daily_stats[date]
            for suite in report.test_suites:
                stats["total_tests"] += suite.total_tests
                stats["passed_tests"] += suite.passed_tests
                stats["failed_tests"] += suite.failed_tests
                stats["skipped_tests"] += suite.skipped_tests
                stats["error_tests"] += suite.error_tests
                stats["healed_tests"] += suite.healed_tests
                stats["total_duration"] += suite.total_duration_ms
            stats["count"] += 1
        
        # Create trends
        for date, stats in sorted(daily_stats.items()):
            trends.append(TestTrend(
                date=datetime.combine(date, datetime.min.time()),
                total_tests=stats["total_tests"],
                passed_tests=stats["passed_tests"],
                failed_tests=stats["failed_tests"],
                skipped_tests=stats["skipped_tests"],
                error_tests=stats["error_tests"],
                healed_tests=stats["healed_tests"],
                avg_duration_ms=stats["total_duration"] // stats["count"],
                failure_rate=(stats["failed_tests"] + stats["error_tests"]) / stats["total_tests"] * 100 if stats["total_tests"] > 0 else 0,
                healing_success_rate=stats["healed_tests"] / (stats["failed_tests"] + stats["healed_tests"]) * 100 if (stats["failed_tests"] + stats["healed_tests"]) > 0 else 0
            ))
        
        return trends
    
    def _format_duration(self, duration_ms: int) -> str:
        """Format duration in milliseconds to human-readable string"""
        seconds = duration_ms / 1000
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    def _save_report(self, report: TestReport):
        """Save report to storage"""
        report_path = self.storage_path / f"report_{report.id}.json"
        with open(report_path, "w") as f:
            json.dump(report.dict(), f, default=str)
    
    def generate_report(
        self,
        test_suites: List[TestSuite],
        title: str,
        description: Optional[str] = None,
        environment: Dict[str, str] = {},
        metadata: Dict[str, Any] = {}
    ) -> TestReport:
        """Generate a comprehensive test report"""
        report = TestReport(
            title=title,
            description=description,
            test_suites=test_suites,
            summary=self._calculate_summary(test_suites),
            trends=self._calculate_trends(),
            environment=environment,
            metadata=metadata,
            version="1.0.0"
        )
        
        self._save_report(report)
        return report
    
    def generate_html_report(self, report: TestReport) -> str:
        """Generate HTML report"""
        template = Template(HTML_TEMPLATE)
        return template.render(report=report)
    
    def generate_markdown_report(self, report: TestReport) -> str:
        """Generate Markdown report"""
        template = Template(MARKDOWN_TEMPLATE)
        return template.render(report=report)
    
    def save_html_report(self, report: TestReport, output_path: Optional[str] = None):
        """Save HTML report to file"""
        if output_path is None:
            output_path = self.storage_path / f"report_{report.id}.html"
        
        html_content = self.generate_html_report(report)
        with open(output_path, "w") as f:
            f.write(html_content)
    
    def save_markdown_report(self, report: TestReport, output_path: Optional[str] = None):
        """Save Markdown report to file"""
        if output_path is None:
            output_path = self.storage_path / f"report_{report.id}.md"
        
        md_content = self.generate_markdown_report(report)
        with open(output_path, "w") as f:
            f.write(md_content)
