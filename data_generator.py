import random
import uuid
from datetime import datetime, timedelta
from typing import List

from models import (
    LotSummary,
    ProductionMetrics,
    SecurityEvent,
    SecurityLevel,
    Tree,
    TreeLocation,
    TreeMetrics,
    TreeStatus,
    WeatherCondition,
    WeatherData,
)


class DataGenerator:
    """Utility class to generate sample data for the cocoa plantation API"""

    def __init__(self, seed: int = 42):
        random.seed(seed)

        # Base coordinates for cocoa plantation region (Brazil - Bahia)
        self.base_lat = -14.2350
        self.base_lon = -42.7816

        # Sample event types and descriptions
        self.event_types = [
            "pest_infestation",
            "disease_outbreak",
            "weather_damage",
            "theft_attempt",
            "equipment_malfunction",
            "irrigation_failure",
        ]

        self.event_descriptions = {
            "pest_infestation": "Cocoa pod borer detected on tree",
            "disease_outbreak": "Witches' broom disease symptoms observed",
            "weather_damage": "Storm damage to branches and pods",
            "theft_attempt": "Unauthorized access detected in area",
            "equipment_malfunction": "Monitoring sensor malfunction",
            "irrigation_failure": "Irrigation system failure in sector",
        }

    def generate_tree_location(self, lot_id: int) -> TreeLocation:
        """Generate a realistic tree location within a lot"""
        # Each lot is roughly 100m x 100m, with lots arranged in a grid
        lot_row = (lot_id - 1) // 4
        lot_col = (lot_id - 1) % 4

        # Base position for this lot
        lot_lat = self.base_lat + (lot_row * 0.001)  # ~100m per 0.001 degrees
        lot_lon = self.base_lon + (lot_col * 0.001)

        # Random position within the lot
        tree_lat = lot_lat + random.uniform(-0.0005, 0.0005)
        tree_lon = lot_lon + random.uniform(-0.0005, 0.0005)
        altitude = random.uniform(200, 400)  # Typical cocoa growing altitude

        return TreeLocation(latitude=tree_lat, longitude=tree_lon, altitude=altitude)

    def generate_tree_metrics(self, tree_age: int) -> TreeMetrics:
        """Generate realistic tree metrics based on age"""
        # Maturity increases with age but plateaus
        maturity_base = min(tree_age * 8, 95)
        maturity_index = max(5, maturity_base + random.uniform(-15, 15))
        maturity_index = min(100, maturity_index)

        # Security events are random but influenced by location
        security_events = random.choices([0, 1, 2, 3], weights=[70, 20, 8, 2])[0]

        # Fungal threat varies by season and conditions
        fungal_threat = random.uniform(15, 85)

        # Canopy grading related to age and health
        canopy_base = min(tree_age * 7, 90)
        canopy_grading = max(10, canopy_base + random.uniform(-20, 20))
        canopy_grading = min(100, canopy_grading)

        # Tree density based on plantation management
        tree_density = random.uniform(30, 80)

        return TreeMetrics(
            maturity_index=round(maturity_index, 1),
            security_events=security_events,
            fungal_threat=round(fungal_threat, 1),
            canopy_grading=round(canopy_grading, 1),
            tree_age=tree_age,
            tree_density=round(tree_density, 1),
        )

    def generate_tree(self, farm_id: str, lot_id: int) -> Tree:
        """Generate a single tree with realistic data"""
        tree_id = "tree_{farm_id}_{lot_id}_{uuid.uuid4().hex[:8]}"
        tree_age = random.randint(3, 25)  # Cocoa trees productive for ~20 years

        # Status based on age and random factors
        if tree_age < 5:
            status = TreeStatus.YOUNG
        elif tree_age > 20:
            status = random.choice([TreeStatus.MATURE, TreeStatus.HEALTHY])
        else:
            status = random.choices(
                [TreeStatus.HEALTHY, TreeStatus.DISEASED, TreeStatus.DAMAGED],
                weights=[80, 15, 5],
            )[0]

        return Tree(
            id=tree_id,
            farm_id=farm_id,
            lot_id=lot_id,
            location=self.generate_tree_location(lot_id),
            metrics=self.generate_tree_metrics(tree_age),
            status=status,
            last_updated=datetime.now() - timedelta(hours=random.randint(1, 48)),
        )

    def generate_lot_summary(self, lot_id: int, trees: List[Tree]) -> LotSummary:
        """Generate lot summary from trees data"""
        total_trees = len(trees)
        healthy_trees = len([t for t in trees if t.status == TreeStatus.HEALTHY])
        security_events = sum(t.metrics.security_events for t in trees)
        avg_maturity = sum(t.metrics.maturity_index for t in trees) / total_trees
        avg_fungal_threat = sum(t.metrics.fungal_threat for t in trees) / total_trees

        return LotSummary(
            lot_id=lot_id,
            total_trees=total_trees,
            healthy_trees=healthy_trees,
            security_events=security_events,
            avg_maturity=round(avg_maturity, 1),
            avg_fungal_threat=round(avg_fungal_threat, 1),
            area_hectares=1.0,  # Each lot is 1 hectare
            last_inspection=datetime.now() - timedelta(days=random.randint(1, 7)),
        )

    def generate_security_event(self, tree: Tree) -> SecurityEvent:
        """Generate a security event for a tree"""
        event_type = random.choice(self.event_types)
        severity = random.choices(
            [
                SecurityLevel.LOW,
                SecurityLevel.MEDIUM,
                SecurityLevel.HIGH,
                SecurityLevel.CRITICAL,
            ],
            weights=[50, 30, 15, 5],
        )[0]

        return SecurityEvent(
            id="event_{uuid.uuid4().hex[:8]}",
            tree_id=tree.id,
            lot_id=tree.lot_id,
            event_type=event_type,
            severity=severity,
            description=self.event_descriptions[event_type],
            location=tree.location,
            timestamp=datetime.now() - timedelta(hours=random.randint(1, 168)),
            resolved=(
                random.choice([True, False])
                if severity != SecurityLevel.CRITICAL
                else False
            ),
        )

    def generate_weather_data(self, lot_id: int) -> WeatherData:
        """Generate weather data for a lot"""
        condition = random.choice(list(WeatherCondition))

        # Temperature varies by condition
        temp_ranges = {
            WeatherCondition.SUNNY: (28, 35),
            WeatherCondition.CLOUDY: (24, 30),
            WeatherCondition.RAINY: (20, 26),
            WeatherCondition.STORMY: (18, 24),
        }

        temp_range = temp_ranges[condition]
        temperature = random.uniform(*temp_range)

        # Humidity and rainfall based on condition
        if condition == WeatherCondition.RAINY:
            humidity = random.uniform(75, 95)
            rainfall = random.uniform(5, 25)
        elif condition == WeatherCondition.STORMY:
            humidity = random.uniform(80, 100)
            rainfall = random.uniform(20, 50)
        else:
            humidity = random.uniform(60, 85)
            rainfall = random.uniform(0, 2)

        wind_speed = random.uniform(5, 25)

        return WeatherData(
            lot_id=lot_id,
            condition=condition,
            temperature=round(temperature, 1),
            humidity=round(humidity, 1),
            rainfall=round(rainfall, 1),
            wind_speed=round(wind_speed, 1),
            timestamp=datetime.now() - timedelta(minutes=random.randint(0, 60)),
        )

    def generate_production_metrics(self, lot_summary: LotSummary) -> ProductionMetrics:
        """Generate production metrics for a lot"""
        # Yield based on tree count and average maturity
        base_yield = lot_summary.total_trees * 15  # ~15kg per tree average
        maturity_factor = lot_summary.avg_maturity / 100
        estimated_yield = base_yield * maturity_factor * random.uniform(0.8, 1.2)

        # Harvest readiness based on maturity
        harvest_readiness = min(100, lot_summary.avg_maturity + random.uniform(-10, 10))

        # Quality score inversely related to fungal threat
        quality_score = (
            100 - (lot_summary.avg_fungal_threat * 0.7) + random.uniform(-5, 5)
        )
        quality_score = max(0, min(100, quality_score))

        # Optimal harvest date based on readiness
        days_to_harvest = max(1, int((100 - harvest_readiness) / 2))
        optimal_harvest_date = datetime.now() + timedelta(days=days_to_harvest)

        return ProductionMetrics(
            lot_id=lot_summary.lot_id,
            estimated_yield=round(estimated_yield, 1),
            harvest_readiness=round(harvest_readiness, 1),
            quality_score=round(quality_score, 1),
            optimal_harvest_date=(
                optimal_harvest_date if harvest_readiness < 95 else None
            ),
        )
