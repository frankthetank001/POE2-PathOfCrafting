"""
Price Estimation Algorithm

Estimates item value based on comparable trade listings, accounting for:
- Roll quality comparison (are listings better or worse than our item?)
- Listing age (newer listings are more reliable)
- Mod tier values (T1 vs T3 has different value impact)
- Price distribution analysis
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from statistics import median, mean
import math

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ModComparison:
    """Comparison of a single mod between our item and a listing."""
    stat_id: str
    our_value: float
    listing_value: float
    t1_max: float  # Maximum possible T1 roll

    @property
    def our_percentile(self) -> float:
        """How good is our roll as a percentile (0-1)."""
        if self.t1_max <= 0:
            return 0.5
        return min(1.0, self.our_value / self.t1_max)

    @property
    def listing_percentile(self) -> float:
        """How good is the listing's roll as a percentile (0-1)."""
        if self.t1_max <= 0:
            return 0.5
        return min(1.0, self.listing_value / self.t1_max)

    @property
    def relative_quality(self) -> float:
        """
        How our item compares to listing.
        > 1 means our item is better
        < 1 means listing is better
        = 1 means equal
        """
        if self.listing_value <= 0:
            return 1.0
        return self.our_value / self.listing_value


@dataclass
class ListingAnalysis:
    """Analysis of a single trade listing compared to our item."""
    price_chaos: float
    indexed_time: Optional[datetime]
    mod_comparisons: List[ModComparison]

    @property
    def age_hours(self) -> float:
        """How old is this listing in hours."""
        if not self.indexed_time:
            return 24.0  # Assume 1 day if unknown
        now = datetime.now(timezone.utc)
        delta = now - self.indexed_time
        return delta.total_seconds() / 3600

    @property
    def age_weight(self) -> float:
        """
        Weight based on listing age.
        Newer listings are weighted higher.
        Decay: 100% at 0h, ~50% at 24h, ~25% at 48h
        """
        hours = self.age_hours
        # Exponential decay with half-life of 24 hours
        return math.exp(-0.693 * hours / 24)

    @property
    def average_relative_quality(self) -> float:
        """Average quality of our item vs this listing across all mods."""
        if not self.mod_comparisons:
            return 1.0
        return mean(mc.relative_quality for mc in self.mod_comparisons)

    @property
    def is_listing_better(self) -> bool:
        """Is the listing's item better than ours overall?"""
        return self.average_relative_quality < 1.0

    @property
    def quality_factor(self) -> float:
        """
        Factor to adjust price based on quality difference.
        If listing is better, our item is worth less (factor < 1)
        If our item is better, it's worth more (factor > 1)
        """
        avg_quality = self.average_relative_quality
        # Use a dampened adjustment to avoid extreme swings
        # quality 0.8 -> factor ~0.9 (our item worth 90% of listing)
        # quality 1.2 -> factor ~1.1 (our item worth 110% of listing)
        return 1.0 + (avg_quality - 1.0) * 0.5


@dataclass
class PriceEstimation:
    """Result of price estimation algorithm."""
    estimated_price: float
    confidence: str  # "high", "medium", "low"
    price_range_low: float
    price_range_high: float

    # Analysis details
    num_listings_analyzed: int
    num_better_listings: int  # Listings with better items than ours
    num_worse_listings: int   # Listings with worse items than ours
    average_listing_age_hours: float

    # The raw prices for reference
    raw_min: float
    raw_median: float
    raw_max: float

    reasoning: str  # Human-readable explanation


class PriceEstimator:
    """
    Estimates item prices using intelligent comparison with trade listings.
    """

    def __init__(self):
        pass

    def estimate(
        self,
        our_item_mods: Dict[str, float],  # stat_id -> our rolled value
        t1_maxes: Dict[str, float],        # stat_id -> T1 max value
        listings: List[Dict[str, Any]],    # Raw listing data from trade API
    ) -> PriceEstimation:
        """
        Estimate the price of our item based on comparable listings.

        Args:
            our_item_mods: Dict mapping stat_id to our item's rolled value
            t1_maxes: Dict mapping stat_id to the T1 maximum for that stat
            listings: List of listing dicts with price_chaos, indexed_time, and mods

        Returns:
            PriceEstimation with estimated price and analysis
        """
        if not listings:
            return self._no_listings_result()

        # Analyze each listing
        analyses = []
        for listing in listings:
            analysis = self._analyze_listing(listing, our_item_mods, t1_maxes)
            if analysis:
                analyses.append(analysis)

        if not analyses:
            return self._no_listings_result()

        # Calculate statistics
        raw_prices = [a.price_chaos for a in analyses]
        raw_min = min(raw_prices)
        raw_max = max(raw_prices)
        raw_median = median(raw_prices)

        num_better = sum(1 for a in analyses if a.is_listing_better)
        num_worse = len(analyses) - num_better
        avg_age = mean(a.age_hours for a in analyses)

        # Calculate weighted price estimate
        estimated_price = self._calculate_weighted_estimate(analyses)

        # Determine confidence
        confidence = self._determine_confidence(analyses, num_better, num_worse)

        # Calculate price range
        price_range_low, price_range_high = self._calculate_price_range(
            analyses, estimated_price, confidence
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            analyses, estimated_price, num_better, num_worse, avg_age
        )

        return PriceEstimation(
            estimated_price=round(estimated_price, 1),
            confidence=confidence,
            price_range_low=round(price_range_low, 1),
            price_range_high=round(price_range_high, 1),
            num_listings_analyzed=len(analyses),
            num_better_listings=num_better,
            num_worse_listings=num_worse,
            average_listing_age_hours=round(avg_age, 1),
            raw_min=raw_min,
            raw_median=raw_median,
            raw_max=raw_max,
            reasoning=reasoning,
        )

    def _analyze_listing(
        self,
        listing: Dict[str, Any],
        our_mods: Dict[str, float],
        t1_maxes: Dict[str, float],
    ) -> Optional[ListingAnalysis]:
        """Analyze a single listing compared to our item."""
        try:
            price_chaos = listing.get("price_chaos", 0)
            if price_chaos <= 0:
                return None

            # Parse indexed time
            indexed_time = None
            if listing.get("indexed_time"):
                try:
                    indexed_time = datetime.fromisoformat(
                        listing["indexed_time"].replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass

            # Compare mods
            mod_comparisons = []
            listing_mods = listing.get("mods", {})  # stat_id -> value

            for stat_id, our_value in our_mods.items():
                listing_value = listing_mods.get(stat_id, 0)
                t1_max = t1_maxes.get(stat_id, our_value)  # Fallback to our value

                mod_comparisons.append(ModComparison(
                    stat_id=stat_id,
                    our_value=our_value,
                    listing_value=listing_value,
                    t1_max=t1_max,
                ))

            return ListingAnalysis(
                price_chaos=price_chaos,
                indexed_time=indexed_time,
                mod_comparisons=mod_comparisons,
            )
        except Exception as e:
            logger.warning(f"Error analyzing listing: {e}")
            return None

    def _calculate_weighted_estimate(self, analyses: List[ListingAnalysis]) -> float:
        """
        Calculate weighted price estimate.

        Weights consider:
        - Listing age (newer = higher weight)
        - Quality similarity (closer to our item = higher weight)
        """
        if not analyses:
            return 0.0

        weighted_sum = 0.0
        weight_total = 0.0

        for analysis in analyses:
            # Base weight from age
            age_weight = analysis.age_weight

            # Adjust weight based on quality similarity
            # Listings with similar quality to ours are more relevant
            quality_diff = abs(analysis.average_relative_quality - 1.0)
            similarity_weight = 1.0 / (1.0 + quality_diff * 2)

            # Combined weight
            weight = age_weight * similarity_weight

            # Adjust price based on quality difference
            adjusted_price = analysis.price_chaos * analysis.quality_factor

            weighted_sum += adjusted_price * weight
            weight_total += weight

        if weight_total <= 0:
            return median(a.price_chaos for a in analyses)

        return weighted_sum / weight_total

    def _determine_confidence(
        self,
        analyses: List[ListingAnalysis],
        num_better: int,
        num_worse: int,
    ) -> str:
        """Determine confidence level in the estimate."""
        num_listings = len(analyses)

        # Need enough listings
        if num_listings < 3:
            return "low"

        # Check listing age - if most are old, lower confidence
        avg_age = mean(a.age_hours for a in analyses)
        if avg_age > 72:  # More than 3 days old on average
            return "low"

        # Check price variance
        prices = [a.price_chaos for a in analyses]
        if len(prices) >= 2:
            price_range = max(prices) - min(prices)
            median_price = median(prices)
            if median_price > 0:
                variance_ratio = price_range / median_price
                if variance_ratio > 2.0:  # Prices vary by more than 200%
                    return "low"
                elif variance_ratio > 1.0:  # Prices vary by more than 100%
                    return "medium"

        # Good number of listings with reasonable variance
        if num_listings >= 8 and avg_age < 48:
            return "high"
        elif num_listings >= 5:
            return "medium"

        return "medium"

    def _calculate_price_range(
        self,
        analyses: List[ListingAnalysis],
        estimated_price: float,
        confidence: str,
    ) -> tuple[float, float]:
        """Calculate price range based on confidence and data."""
        # Base range on confidence
        if confidence == "high":
            range_factor = 0.15  # ±15%
        elif confidence == "medium":
            range_factor = 0.30  # ±30%
        else:
            range_factor = 0.50  # ±50%

        # Also consider actual price distribution
        prices = [a.price_chaos for a in analyses]
        if len(prices) >= 3:
            sorted_prices = sorted(prices)
            # Use 10th and 90th percentile as bounds
            low_idx = max(0, int(len(sorted_prices) * 0.1))
            high_idx = min(len(sorted_prices) - 1, int(len(sorted_prices) * 0.9))
            data_low = sorted_prices[low_idx]
            data_high = sorted_prices[high_idx]

            # Blend estimated range with data range
            est_low = estimated_price * (1 - range_factor)
            est_high = estimated_price * (1 + range_factor)

            range_low = (est_low + data_low) / 2
            range_high = (est_high + data_high) / 2
        else:
            range_low = estimated_price * (1 - range_factor)
            range_high = estimated_price * (1 + range_factor)

        return max(0, range_low), range_high

    def _generate_reasoning(
        self,
        analyses: List[ListingAnalysis],
        estimated_price: float,
        num_better: int,
        num_worse: int,
        avg_age: float,
    ) -> str:
        """Generate human-readable reasoning for the estimate."""
        parts = []

        total = len(analyses)
        parts.append(f"Based on {total} comparable listings")

        if num_better > num_worse:
            parts.append(
                f"{num_better}/{total} listings have better rolls, "
                "suggesting your item is below average"
            )
        elif num_worse > num_better:
            parts.append(
                f"{num_worse}/{total} listings have worse rolls, "
                "suggesting your item is above average"
            )
        else:
            parts.append("listings have similar quality to your item")

        if avg_age > 48:
            parts.append(f"(avg listing age: {avg_age:.0f}h - may be stale)")
        elif avg_age < 12:
            parts.append(f"(avg listing age: {avg_age:.0f}h - recent data)")

        return ". ".join(parts) + "."

    def _no_listings_result(self) -> PriceEstimation:
        """Return result when no listings available."""
        return PriceEstimation(
            estimated_price=0,
            confidence="low",
            price_range_low=0,
            price_range_high=0,
            num_listings_analyzed=0,
            num_better_listings=0,
            num_worse_listings=0,
            average_listing_age_hours=0,
            raw_min=0,
            raw_median=0,
            raw_max=0,
            reasoning="No comparable listings found.",
        )


# Singleton instance
_price_estimator: Optional[PriceEstimator] = None


def get_price_estimator() -> PriceEstimator:
    """Get or create the price estimator singleton."""
    global _price_estimator
    if _price_estimator is None:
        _price_estimator = PriceEstimator()
    return _price_estimator
