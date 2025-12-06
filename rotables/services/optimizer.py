# rotables/services/optimizer.py

"""
Cost-aware optimizer for kit loading and purchasing decisions.

Key optimization considerations:
1. Minimize penalty costs (unfulfilled passengers, overstock, understock)
2. Minimize operational costs (loading, movement, processing)
3. Balance inventory across network
4. Plan purchases with lead time consideration
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from rotables.models.state import GameState, KIT_INFO
from rotables.dto.dto import FlightEvent, PerClassAmount


@dataclass
class LoadDecision:
    """Decision for how many kits to load on a flight."""
    flight_id: str
    fc: int = 0
    bc: int = 0
    pe: int = 0
    ec: int = 0
    
    def total_kits(self) -> int:
        return self.fc + self.bc + self.pe + self.ec


@dataclass
class PurchaseDecision:
    """Decision for how many kits to purchase at hub."""
    fc: int = 0
    bc: int = 0
    pe: int = 0
    ec: int = 0
    
    def total_cost(self) -> float:
        return (
            self.fc * KIT_INFO["fc"]["cost"] +
            self.bc * KIT_INFO["bc"]["cost"] +
            self.pe * KIT_INFO["pe"]["cost"] +
            self.ec * KIT_INFO["ec"]["cost"]
        )


class Optimizer:
    """
    Optimizes kit loading and purchasing decisions to minimize total cost.
    """
    
    # Penalty factors from README
    NEGATIVE_INVENTORY_FACTOR = 1000.0
    OVER_CAPACITY_FACTOR = 100.0
    FLIGHT_OVERLOAD_FACTOR = 10.0
    UNFULFILLED_PASSENGERS_FACTOR = 5.0
    
    def __init__(self, state: GameState):
        self.state = state
    
    def calculate_load_cost(self, ev: FlightEvent, fc: int, bc: int, pe: int, ec: int) -> float:
        """
        Calculate the operational cost for loading kits onto a flight.
        
        Total cost = Loading Cost + Movement Cost + Processing Cost
        """
        origin = ev.origin_airport
        destination = ev.destination_airport
        distance = ev.distance if ev.distance > 0 else 1000  # Default fallback
        
        origin_data = self.state.airports_data.get(origin, {})
        dest_data = self.state.airports_data.get(destination, {})
        
        # Loading costs at origin
        loading_cost = (
            fc * origin_data.get("loading_cost_fc", 1.0) +
            bc * origin_data.get("loading_cost_bc", 1.0) +
            pe * origin_data.get("loading_cost_pe", 1.0) +
            ec * origin_data.get("loading_cost_ec", 1.0)
        )
        
        # Movement cost (weight * distance * fuel cost per km)
        # Assume fuel cost ~0.01 per km per kg
        fuel_cost_per_km = 0.01
        total_weight = (
            fc * KIT_INFO["fc"]["weight"] +
            bc * KIT_INFO["bc"]["weight"] +
            pe * KIT_INFO["pe"]["weight"] +
            ec * KIT_INFO["ec"]["weight"]
        )
        movement_cost = distance * fuel_cost_per_km * total_weight
        
        # Processing costs at destination
        processing_cost = (
            fc * dest_data.get("processing_cost_fc", 0.5) +
            bc * dest_data.get("processing_cost_bc", 0.5) +
            pe * dest_data.get("processing_cost_pe", 0.5) +
            ec * dest_data.get("processing_cost_ec", 0.5)
        )
        
        return loading_cost + movement_cost + processing_cost
    
    def calculate_unfulfilled_penalty(self, ev: FlightEvent, 
                                       fc_loaded: int, bc_loaded: int, 
                                       pe_loaded: int, ec_loaded: int) -> float:
        """Calculate penalty for passengers without kits."""
        distance = ev.distance if ev.distance > 0 else 1000
        
        fc_short = max(0, ev.passengers.first - fc_loaded)
        bc_short = max(0, ev.passengers.business - bc_loaded)
        pe_short = max(0, ev.passengers.premium_economy - pe_loaded)
        ec_short = max(0, ev.passengers.economy - ec_loaded)
        
        penalty = self.UNFULFILLED_PASSENGERS_FACTOR * distance * (
            fc_short * KIT_INFO["fc"]["cost"] +
            bc_short * KIT_INFO["bc"]["cost"] +
            pe_short * KIT_INFO["pe"]["cost"] +
            ec_short * KIT_INFO["ec"]["cost"]
        )
        
        return penalty
    
    def optimize_load(self, ev: FlightEvent) -> LoadDecision:
        """
        Determine optimal kit load for a flight.
        
        Strategy:
        1. Load exactly as many kits as passengers need (avoiding overage)
        2. Constrained by:
           - Available inventory at origin
           - Aircraft kit capacity
        3. Prioritize high-value classes (first > business > premium > economy)
        """
        origin = ev.origin_airport
        inv = self.state.inventory.get(origin)
        ac_caps = self.state.aircraft_caps.get(ev.aircraft_type, {})
        
        if not inv:
            return LoadDecision(flight_id=str(ev.flight_id))
        
        # Calculate optimal load per class
        def optimal_load(need: int, capacity: int, available: int) -> int:
            """Load exactly what's needed, within constraints."""
            return min(need, capacity, max(0, available))
        
        fc_load = optimal_load(ev.passengers.first, ac_caps.get("fc", 0), inv.fc)
        bc_load = optimal_load(ev.passengers.business, ac_caps.get("bc", 0), inv.bc)
        pe_load = optimal_load(ev.passengers.premium_economy, ac_caps.get("pe", 0), inv.pe)
        ec_load = optimal_load(ev.passengers.economy, ac_caps.get("ec", 0), inv.ec)
        
        return LoadDecision(
            flight_id=str(ev.flight_id),
            fc=fc_load,
            bc=bc_load,
            pe=pe_load,
            ec=ec_load
        )
    
    def calculate_hub_purchase_need(self, day: int, hour: int) -> PurchaseDecision:
        """
        Calculate how many kits to purchase at the hub.
        
        Strategy:
        1. Look at forecasted demand over next 48 hours
        2. Consider inventory + pending arrivals
        3. Purchase if shortfall predicted
        4. Account for lead time (24 hours)
        """
        hub_id = self.state.hub_id
        if not hub_id:
            return PurchaseDecision()
        
        # Look ahead for demand (48 hours to account for lead time)
        horizon_hours = 48
        demand = self.state.get_forecasted_demand(hub_id, day, hour, horizon_hours)
        
        # Get effective inventory (current + pending within horizon)
        effective = self.state.get_effective_inventory(hub_id, day, hour, horizon_hours)
        
        # Calculate shortfall
        fc_shortfall = max(0, demand["fc"] - effective["fc"])
        bc_shortfall = max(0, demand["bc"] - effective["bc"])
        pe_shortfall = max(0, demand["pe"] - effective["pe"])
        ec_shortfall = max(0, demand["ec"] - effective["ec"])
        
        # Add safety buffer (20%)
        safety_factor = 1.2
        
        # Only purchase if significant shortfall
        min_purchase_threshold = 5
        
        fc_purchase = int(fc_shortfall * safety_factor) if fc_shortfall > min_purchase_threshold else 0
        bc_purchase = int(bc_shortfall * safety_factor) if bc_shortfall > min_purchase_threshold else 0
        pe_purchase = int(pe_shortfall * safety_factor) if pe_shortfall > min_purchase_threshold else 0
        ec_purchase = int(ec_shortfall * safety_factor) if ec_shortfall > min_purchase_threshold else 0
        
        return PurchaseDecision(
            fc=fc_purchase,
            bc=bc_purchase,
            pe=pe_purchase,
            ec=ec_purchase
        )
    
    def should_purchase_proactively(self, day: int, hour: int) -> bool:
        """
        Determine if we should proactively purchase kits.
        
        Purchase early in the game to build buffer, less towards end.
        """
        total_hours = day * 24 + hour
        max_hours = 30 * 24  # 30 days
        
        # More aggressive purchasing in first 10 days
        if total_hours < 10 * 24:
            return True
        
        # Moderate purchasing in days 10-20
        if total_hours < 20 * 24:
            return total_hours % 6 == 0  # Every 6 hours
        
        # Conservative near end (avoid end-of-game penalties)
        return False
