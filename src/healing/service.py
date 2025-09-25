"""
Service layer for the self-healing test mechanism.
"""

from typing import List, Optional, Dict, Tuple
from playwright.sync_api import Page
from .models import (
    ElementSnapshot, HealingAttempt, HealingHistory,
    HealingStats, LocatorType
)
from .strategies import (
    TextSimilarityStrategy,
    AttributeBasedStrategy,
    XPathStrategy
)
import json
from pathlib import Path
from datetime import datetime

class HealingService:
    def __init__(self, storage_path: str = "./data/healing"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize healing strategies
        self.strategies = [
            AttributeBasedStrategy(),
            TextSimilarityStrategy(),
            XPathStrategy()
        ]
        
        # Load healing history
        self.healing_history: Dict[str, HealingHistory] = self._load_history()
        self.stats = self._calculate_stats()
        
    def _load_history(self) -> Dict[str, HealingHistory]:
        """Load healing history from storage"""
        history = {}
        if (self.storage_path / "healing_history.json").exists():
            with open(self.storage_path / "healing_history.json", "r") as f:
                data = json.load(f)
                for item in data:
                    history_item = HealingHistory(**item)
                    history[history_item.original_locator] = history_item
        return history
    
    def _save_history(self):
        """Save healing history to storage"""
        with open(self.storage_path / "healing_history.json", "w") as f:
            json.dump(
                [history.dict() for history in self.healing_history.values()],
                f,
                default=str
            )
    
    def _calculate_stats(self) -> HealingStats:
        """Calculate healing statistics"""
        stats = HealingStats()
        
        for history in self.healing_history.values():
            for attempt in history.healing_attempts:
                stats.total_attempts += 1
                if attempt.success:
                    stats.successful_attempts += 1
                else:
                    stats.failed_attempts += 1
                    
                # Update strategy success rates
                if attempt.strategy_used not in stats.strategy_success_rates:
                    stats.strategy_success_rates[attempt.strategy_used] = 0
                current_rate = stats.strategy_success_rates[attempt.strategy_used]
                stats.strategy_success_rates[attempt.strategy_used] = (
                    current_rate + (1 if attempt.success else 0)
                ) / 2
                
                stats.average_confidence_score += attempt.confidence_score
                
        if stats.total_attempts > 0:
            stats.average_confidence_score /= stats.total_attempts
            
        stats.healing_history = list(self.healing_history.values())
        return stats
    
    async def heal_locator(
        self,
        page: Page,
        locator: str,
        snapshot: ElementSnapshot
    ) -> Tuple[Optional[str], float]:
        """
        Attempt to heal a broken locator using multiple strategies.
        Returns the best healed locator and confidence score.
        """
        best_locator = None
        best_confidence = 0.0
        successful_strategy = None
        
        # Try each strategy
        for strategy in self.strategies:
            healed_locator, confidence = await strategy.heal(page, snapshot)
            
            # Apply strategy weight
            weighted_confidence = confidence * strategy.weight
            
            if healed_locator and weighted_confidence > best_confidence:
                # Verify the healed locator works
                try:
                    element = await page.wait_for_selector(healed_locator, timeout=1000)
                    if element:
                        best_locator = healed_locator
                        best_confidence = weighted_confidence
                        successful_strategy = strategy.name
                except:
                    continue
        
        # Record healing attempt
        attempt = HealingAttempt(
            original_locator=locator,
            healed_locator=best_locator,
            success=best_locator is not None,
            strategy_used=successful_strategy or "none",
            confidence_score=best_confidence
        )
        
        # Update history
        if locator not in self.healing_history:
            self.healing_history[locator] = HealingHistory(
                original_locator=locator,
                element_snapshot=snapshot
            )
        
        history = self.healing_history[locator]
        history.healing_attempts.append(attempt)
        
        if best_locator:
            history.last_successful_locator = best_locator
            history.last_success_timestamp = datetime.now()
        
        # Save and update stats
        self._save_history()
        self.stats = self._calculate_stats()
        
        return best_locator, best_confidence
    
    def get_stats(self) -> HealingStats:
        """Get current healing statistics"""
        return self.stats
    
    def get_history(self, locator: str) -> Optional[HealingHistory]:
        """Get healing history for a specific locator"""
        return self.healing_history.get(locator)
