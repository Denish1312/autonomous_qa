"""
Risk analysis system for test prioritization and quality assessment.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel
import numpy as np
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
import os

class DefectMetrics(BaseModel):
    """Metrics for defect analysis"""
    total_defects: int
    critical_defects: int
    high_defects: int
    medium_defects: int
    low_defects: int
    avg_time_to_fix: float  # in hours
    defect_density: float  # defects per 1000 lines of code
    regression_rate: float  # percentage of defects that are regressions

class RiskFactors(BaseModel):
    """Risk factors for feature analysis"""
    complexity_score: float
    change_frequency: float
    defect_history: float
    test_coverage: float
    impact_score: float

class RiskScore(BaseModel):
    """Comprehensive risk score for a feature"""
    feature_name: str
    overall_score: float
    risk_factors: RiskFactors
    defect_metrics: DefectMetrics
    last_updated: datetime
    confidence_score: float

class RiskAnalyzer:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.qdrant = Qdrant.from_existing_collection(
            embedding=self.embeddings,
            collection_name="historical_defects",
            url=os.getenv("QDRANT_URL", "http://localhost:6333")
        )
    
    async def calculate_risk_score(
        self,
        feature: str,
        codebase_metrics: Optional[Dict[str, float]] = None
    ) -> RiskScore:
        """
        Calculate comprehensive risk score for a feature based on multiple factors.
        
        Args:
            feature: Feature name or description
            codebase_metrics: Optional metrics about the codebase (LOC, etc.)
        
        Returns:
            RiskScore object with detailed risk analysis
        """
        # Get historical defects
        defect_history = await self._get_defect_history(feature)
        
        # Calculate defect metrics
        defect_metrics = await self._calculate_defect_metrics(defect_history)
        
        # Calculate risk factors
        risk_factors = await self._calculate_risk_factors(
            feature,
            defect_history,
            defect_metrics,
            codebase_metrics
        )
        
        # Calculate overall risk score
        overall_score = await self._calculate_overall_score(risk_factors, defect_metrics)
        
        # Calculate confidence score
        confidence_score = await self._calculate_confidence_score(
            defect_history,
            codebase_metrics
        )
        
        return RiskScore(
            feature_name=feature,
            overall_score=overall_score,
            risk_factors=risk_factors,
            defect_metrics=defect_metrics,
            last_updated=datetime.now(),
            confidence_score=confidence_score
        )
    
    async def _get_defect_history(self, feature: str) -> List[Dict]:
        """Retrieve relevant defect history from Qdrant"""
        results = self.qdrant.similarity_search_with_score(
            feature,
            k=50  # Get top 50 similar defects
        )
        
        defects = []
        for doc, score in results:
            if score > 0.7:  # Only consider highly relevant defects
                defects.append({
                    "content": doc.page_content,
                    "similarity": score,
                    "metadata": doc.metadata
                })
        
        return defects
    
    async def _calculate_defect_metrics(
        self,
        defect_history: List[Dict]
    ) -> DefectMetrics:
        """Calculate metrics from defect history"""
        total = len(defect_history)
        if total == 0:
            return DefectMetrics(
                total_defects=0,
                critical_defects=0,
                high_defects=0,
                medium_defects=0,
                low_defects=0,
                avg_time_to_fix=0.0,
                defect_density=0.0,
                regression_rate=0.0
            )
        
        # Count defects by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        fix_times = []
        regressions = 0
        
        for defect in defect_history:
            metadata = defect["metadata"]
            severity_counts[metadata.get("severity", "medium")] += 1
            
            if metadata.get("time_to_fix"):
                fix_times.append(float(metadata["time_to_fix"]))
            
            if metadata.get("is_regression", False):
                regressions += 1
        
        return DefectMetrics(
            total_defects=total,
            critical_defects=severity_counts["critical"],
            high_defects=severity_counts["high"],
            medium_defects=severity_counts["medium"],
            low_defects=severity_counts["low"],
            avg_time_to_fix=np.mean(fix_times) if fix_times else 0.0,
            defect_density=total / 1000,  # Assuming 1000 LOC as base
            regression_rate=regressions / total if total > 0 else 0.0
        )
    
    async def _calculate_risk_factors(
        self,
        feature: str,
        defect_history: List[Dict],
        defect_metrics: DefectMetrics,
        codebase_metrics: Optional[Dict[str, float]]
    ) -> RiskFactors:
        """Calculate risk factors for the feature"""
        # Complexity score (0-1)
        complexity_score = await self._calculate_complexity_score(
            feature,
            codebase_metrics
        )
        
        # Change frequency (0-1)
        change_frequency = await self._calculate_change_frequency(
            feature,
            defect_history
        )
        
        # Defect history score (0-1)
        defect_history_score = (
            (defect_metrics.critical_defects * 1.0 +
             defect_metrics.high_defects * 0.7 +
             defect_metrics.medium_defects * 0.4 +
             defect_metrics.low_defects * 0.1) /
            (defect_metrics.total_defects if defect_metrics.total_defects > 0 else 1)
        )
        
        # Test coverage (0-1)
        test_coverage = await self._calculate_test_coverage(
            feature,
            codebase_metrics
        )
        
        # Impact score (0-1)
        impact_score = await self._calculate_impact_score(
            feature,
            defect_history
        )
        
        return RiskFactors(
            complexity_score=complexity_score,
            change_frequency=change_frequency,
            defect_history=defect_history_score,
            test_coverage=test_coverage,
            impact_score=impact_score
        )
    
    async def _calculate_complexity_score(
        self,
        feature: str,
        codebase_metrics: Optional[Dict[str, float]]
    ) -> float:
        """Calculate complexity score based on code metrics"""
        if not codebase_metrics:
            return 0.5  # Default medium complexity
            
        # Normalize and combine various complexity metrics
        factors = [
            codebase_metrics.get("cyclomatic_complexity", 5) / 10,  # Normalize to 0-1
            codebase_metrics.get("cognitive_complexity", 15) / 30,
            codebase_metrics.get("lines_of_code", 500) / 1000,
            codebase_metrics.get("dependency_count", 10) / 20
        ]
        
        return np.mean(factors)
    
    async def _calculate_change_frequency(
        self,
        feature: str,
        defect_history: List[Dict]
    ) -> float:
        """Calculate change frequency score"""
        if not defect_history:
            return 0.0
            
        # Calculate changes per month
        changes = len(set(d["metadata"].get("commit_id") for d in defect_history))
        months = len(set(d["metadata"].get("month") for d in defect_history))
        
        if months == 0:
            return 0.0
            
        changes_per_month = changes / months
        return min(changes_per_month / 10, 1.0)  # Normalize to 0-1
    
    async def _calculate_test_coverage(
        self,
        feature: str,
        codebase_metrics: Optional[Dict[str, float]]
    ) -> float:
        """Calculate test coverage score"""
        if not codebase_metrics:
            return 0.5  # Default medium coverage
            
        coverage = codebase_metrics.get("test_coverage", 70) / 100
        return coverage
    
    async def _calculate_impact_score(
        self,
        feature: str,
        defect_history: List[Dict]
    ) -> float:
        """Calculate business impact score"""
        if not defect_history:
            return 0.5  # Default medium impact
            
        # Calculate based on defect impact levels
        impact_levels = [d["metadata"].get("impact", "medium") for d in defect_history]
        impact_scores = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.1
        }
        
        return np.mean([impact_scores[level] for level in impact_levels])
    
    async def _calculate_overall_score(
        self,
        risk_factors: RiskFactors,
        defect_metrics: DefectMetrics
    ) -> float:
        """Calculate overall risk score"""
        # Weighted combination of risk factors
        weights = {
            "complexity": 0.2,
            "change_frequency": 0.15,
            "defect_history": 0.25,
            "test_coverage": 0.2,
            "impact": 0.2
        }
        
        score = (
            weights["complexity"] * risk_factors.complexity_score +
            weights["change_frequency"] * risk_factors.change_frequency +
            weights["defect_history"] * risk_factors.defect_history +
            weights["test_coverage"] * (1 - risk_factors.test_coverage) +  # Invert as lower coverage = higher risk
            weights["impact"] * risk_factors.impact_score
        )
        
        return min(max(score, 0.0), 1.0)  # Ensure score is between 0 and 1
    
    async def _calculate_confidence_score(
        self,
        defect_history: List[Dict],
        codebase_metrics: Optional[Dict[str, float]]
    ) -> float:
        """Calculate confidence score in the risk assessment"""
        factors = []
        
        # Data quantity factor
        if len(defect_history) > 20:
            factors.append(1.0)
        elif len(defect_history) > 10:
            factors.append(0.8)
        elif len(defect_history) > 5:
            factors.append(0.6)
        else:
            factors.append(0.4)
        
        # Data recency factor
        if defect_history:
            latest_date = max(
                datetime.fromisoformat(d["metadata"].get("date", "2000-01-01"))
                for d in defect_history
            )
            months_old = (datetime.now() - latest_date).days / 30
            recency_score = max(1.0 - (months_old / 12), 0.0)  # Decay over 12 months
            factors.append(recency_score)
        
        # Metrics availability factor
        if codebase_metrics:
            metrics_coverage = len(codebase_metrics) / 10  # Assume 10 possible metrics
            factors.append(metrics_coverage)
        else:
            factors.append(0.3)
        
        return np.mean(factors)
