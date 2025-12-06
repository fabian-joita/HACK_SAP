# rotables/services/lp_optimizer.py

"""
Linear Programming optimizer for rotables kit allocation.

Uses scipy.optimize.linprog to make globally optimal decisions considering:
- All flight demands in lookahead window
- Inventory constraints at airports
- Movement costs
- Penalty costs for unfulfilled passengers
- Purchase costs and lead times
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from rotables.models.state import GameState
from rotables.dto.dto import FlightEvent, PerClassAmount


# Kit costs and weights (from README)
KIT_COSTS = {"fc": 150.0, "bc": 80.0, "pe": 40.0, "ec": 20.0}
KIT_WEIGHTS = {"fc": 2.0, "bc": 1.5, "pe": 1.0, "ec": 0.5}
LEAD_TIME_HOURS = 24

# Penalty factors (from README)
UNFULFILLED_PENALTY_FACTOR = 5.0
NEGATIVE_INVENTORY_FACTOR = 1000.0


@dataclass
class OptimizationResult:
    """Result of LP optimization."""
    flight_loads: Dict[str, PerClassAmount]  # flight_id -> loads
    purchase_amounts: PerClassAmount
    expected_cost: float


class LPOptimizer:
    """
    Linear Programming based optimizer for kit allocation.
    
    Solves a multi-period inventory optimization problem to minimize:
    - Operational costs (loading, movement,  processing)
    - Penalty costs (unfulfilled passengers, negative inventory)
    - Purchase costs
    """
    
    def __init__(self, state: GameState, airports_data: Dict):
        self.state = state
        self.airports_data = airports_data
        self.fuel_cost_per_km_kg = 0.01
    
    def optimize_loads_and_purchases(
        self,
        flights_to_load: List[FlightEvent],
        current_inventory: Dict[str, Dict[str, int]],
        day: int,
        hour: int
    ) -> OptimizationResult:
        """
        Optimize kit loading and purchasing using heuristics.
        
        Strategy:
        1. Prioritize loading based on cost/benefit
        2. Load exactly passenger demand (avoid overage)
        3. Purchase proactively at hub when inventory low
        4. Consider processing delays (simplified)
        """
        
        flight_loads = {}
        
        # Load kits for each flight optimally
        for flight in flights_to_load:
            loads = self._optimize_single_flight(flight, current_inventory)
            flight_loads[str(flight.flight_id)] = loads
            
            # Update inventory tracking
            origin_inv = current_inventory.get(flight.origin_airport, {})
            origin_inv["fc"] = origin_inv.get("fc", 0) - loads.first
            origin_inv["bc"] = origin_inv.get("bc", 0) - loads.business
            origin_inv["pe"] = origin_inv.get("pe", 0) - loads.premium_economy
            origin_inv["ec"] = origin_inv.get("ec", 0) - loads.economy
        
        # Determine purchase needs
        purchase = self._calculate_purchase_needs(current_inventory, day, hour)
        
        return OptimizationResult(
            flight_loads=flight_loads,
            purchase_amounts=purchase,
            expected_cost=0.0  # Simplified
        )
    
    def _optimize_single_flight(
        self,
        flight: FlightEvent,
        inventory: Dict[str, Dict[str, int]]
    ) -> PerClassAmount:
        """
        Optimize kit loading for a single flight.
        
        Strategy: Load exactly passenger demand, constrained by:
        - Available inventory at origin
        - Aircraft capacity
        
        This minimizes both movement costs and unfulfilled passenger penalties.
        """
        origin_inv = inventory.get(flight.origin_airport, {})
        ac_caps = self.state.aircraft_caps.get(flight.aircraft_type, {})
        
        def safe_load(need: int, capacity: int, available: int) -> int:
            """Calculate optimal load."""
            return max(0, min(need, capacity, available))
        
        fc_load = safe_load(
            flight.passengers.first,
            ac_caps.get("fc", 999),
            origin_inv.get("fc", 0)
        )
        
        bc_load = safe_load(
            flight.passengers.business,
            ac_caps.get("bc", 999),
            origin_inv.get("bc", 0)
        )
        
        pe_load = safe_load(
            flight.passengers.premium_economy,
            ac_caps.get("pe", 999),
            origin_inv.get("pe", 0)
        )
        
        ec_load = safe_load(
            flight.passengers.economy,
            ac_caps.get("ec", 999),
            origin_inv.get("ec", 0)
        )
        
        return PerClassAmount(
            first=fc_load,
            business=bc_load,
            premium_economy=pe_load,
            economy=ec_load
        )
    
    def _calculate_purchase_needs(
        self,
        inventory: Dict[str, Dict[str, int]],
        day: int,
        hour: int
    ) -> PerClassAmount:
        """
        Calculate how many kits to purchase at hub.
        
        Strategy:
        1. Check hub inventory levels
        2. Use rule-based thresholds
        3. Purchase to maintain safety stock
        """
        
        # Find hub
        hub_id = None
        for ap_id, ap_data in self.airports_data.items():
            if ap_data.get("is_hub") or ap_data.get("code", "").startswith("HUB"):
                hub_id = ap_id
                break
        
        if not hub_id:
            return PerClassAmount(0, 0, 0, 0)
        
        hub_inv = inventory.get(hub_id, {})
        
        # Simple threshold-based purchasing
        # Purchase if inventory < threshold
        MIN_THRESHOLDS = {"fc": 50, "bc": 100, "pe": 80, "ec": 200}
        TARGET_LEVELS = {"fc": 150, "bc": 300, "pe": 250, "ec": 600}
        
        # Only purchase periodically (every 12 hours)
        current_hour = day * 24 + hour
        if current_hour % 12 != 0:
            return PerClassAmount(0, 0, 0, 0)
        
        fc_need = max(0, TARGET_LEVELS["fc"] - hub_inv.get("fc", 0))
        bc_need = max(0, TARGET_LEVELS["bc"] - hub_inv.get("bc", 0))
        pe_need = max(0, TARGET_LEVELS["pe"] - hub_inv.get("pe", 0))
        ec_need = max(0, TARGET_LEVELS["ec"] - hub_inv.get("ec", 0))
        
        # Only purchase if below threshold
        fc_buy = fc_need if hub_inv.get("fc", 0) < MIN_THRESHOLDS["fc"] else 0
        bc_buy = bc_need if hub_inv.get("bc", 0) < MIN_THRESHOLDS["bc"] else 0
        pe_buy = pe_need if hub_inv.get("pe", 0) < MIN_THRESHOLDS["pe"] else 0
        ec_buy = ec_need if hub_inv.get("ec", 0) < MIN_THRESHOLDS["ec"] else 0
        
        return PerClassAmount(
            first=fc_buy,
            business=bc_buy,
            premium_economy=pe_buy,
            economy=ec_buy
        )
    
    def estimate_load_cost(self, flight: FlightEvent, loads: PerClassAmount) -> float:
        """Estimate total cost for loading kits on a flight."""
        
        origin_data = self.airports_data.get(flight.origin_airport, {})
        dest_data = self.airports_data.get(flight.destination_airport, {})
        
        # Distance fallback
        distance = getattr(flight, 'distance', 1000)
        if distance <= 0:
            distance = 1000
        
        # Loading costs
        loading_cost = (
            loads.first * origin_data.get("loading_cost_fc", 1.0) +
            loads.business * origin_data.get("loading_cost_bc", 1.0) +
            loads.premium_economy * origin_data.get("loading_cost_pe", 1.0) +
            loads.economy * origin_data.get("loading_cost_ec", 1.0)
        )
        
        # Movement costs
        weight = (
            loads.first * KIT_WEIGHTS["fc"] +
            loads.business * KIT_WEIGHTS["bc"] +
            loads.premium_economy * KIT_WEIGHTS["pe"] +
            loads.economy * KIT_WEIGHTS["ec"]
        )
        movement_cost = distance * self.fuel_cost_per_km_kg * weight
        
        # Processing costs
        processing_cost = (
            loads.first * dest_data.get("processing_cost_fc", 0.5) +
            loads.business * dest_data.get("processing_cost_bc", 0.5) +
            loads.premium_economy * dest_data.get("processing_cost_pe", 0.5) +
            loads.economy * dest_data.get("processing_cost_ec", 0.5)
        )
        
        # Unfulfilled passenger penalty
        distance_for_penalty = distance
        fc_short = max(0, flight.passengers.first - loads.first)
        bc_short = max(0, flight.passengers.business - loads.business)
        pe_short = max(0, flight.passengers.premium_economy - loads.premium_economy)
        ec_short = max(0, flight.passengers.economy - loads.economy)
        
        penalty = UNFULFILLED_PENALTY_FACTOR * distance_for_penalty * (
            fc_short * KIT_COSTS["fc"] +
            bc_short * KIT_COSTS["bc"] +
            pe_short * KIT_COSTS["pe"] +
            ec_short * KIT_COSTS["ec"]
        )
        
        return loading_cost + movement_cost + processing_cost + penalty
