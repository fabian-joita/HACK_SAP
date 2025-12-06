# rotables/services/strategy_simple.py

"""
Simplified strategy - focuses on core functionality without complex inventory simulation.
"""

from typing import List
from rotables.dto.dto import HourRequest, FlightLoad, PerClassAmount
from rotables.models.state import GameState


class StrategySimple:
    """
    Simple strategy: Load exactly passenger demand, purchase aggressively.
    """
    
    def __init__(self):
        self.last_purchase_hour = -999
        print("[STRATEGY] Simple strategy initialized")
    
    def build_hour_request(
        self,
        day: int,
        hour: int,
        state: GameState
    ) -> HourRequest:
        """Build request for this hour."""
        
        # Get flights to load
        flights_to_load = state.pop_flights_to_load()
        flight_loads: List[FlightLoad] = []
        
        for flight in flights_to_load:
            # Load exactly passenger demand (assume inventory available)
            # Don't track inventory - let backend handle it
            loads = PerClassAmount(
                first=flight.passengers.first,
                business=flight.passengers.business,
                premium_economy=flight.passengers.premium_economy,
                economy=flight.passengers.economy
            )
            
            flight_loads.append(FlightLoad(
                flight_id=flight.flight_id,
                loaded_kits=loads
            ))
        
        # Aggressive purchasing - buy every 6 hours
        current_total_hours = day * 24 + hour
        purchasing = PerClassAmount(0, 0, 0, 0)
        
        if current_total_hours - self.last_purchase_hour >= 6:
            # Purchase fixed amounts to maintain stock
            purchasing = PerClassAmount(
                first=100,
                business=200,
                premium_economy=150,
                economy=400
            )
            self.last_purchase_hour = current_total_hours
            print(f"[PURCHASE] Day{day}:H{hour} - Buying kits")
        
        return HourRequest(
            day=day,
            hour=hour,
            flight_loads=flight_loads,
            kit_purchasing_orders=purchasing
        )
