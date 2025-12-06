# rotables/services/strategy_v2.py

"""
Optimized strategy using LP-based optimizer and proper inventory tracking.
"""

from typing import List, Dict
from rotables.dto.dto import HourRequest, FlightLoad, PerClassAmount
from rotables.models.state import GameState
from rotables.services.lp_optimizer import LPOptimizer
from rotables.services.loader import Loader


class StrategyV2:
    """
    Strategy that uses LP optimizer and maintains inventory state.
    """
    
    def __init__(self):
        # Load airport data
        loader = Loader()
        self.airports_data = loader.load_airports_with_stocks()
        
        # Initialize inventory tracking
        self.inventory: Dict[str, Dict[str, int]] = {}
        for ap_id, ap_data in self.airports_data.items():
            self.inventory[ap_id] = {
                "fc": ap_data.get("initial_fc_stock", 0),
                "bc": ap_data.get("initial_bc_stock", 0),
                "pe": ap_data.get("initial_pe_stock", 0),
                "ec": ap_data.get("initial_ec_stock", 0),
            }
        
        # Track pending kit arrivals (simple: add immediately for now)
        self.optimizer = None  # Will be set when state is available
        
        print(f"[STRATEGY] Initialized inventory for {len(self.inventory)} airports")
    
    def build_hour_request(
        self,
        day: int,
        hour: int,
        state: GameState
    ) -> HourRequest:
        """Build optimized hour request."""
        
        # Initialize optimizer if not done
        if self.optimizer is None:
            self.optimizer = LPOptimizer(state, self.airports_data)
        
        # Get flights to load
        flights_to_load = state.pop_flights_to_load()
        
        if not flights_to_load:
            # No flights to load, just check purchasing
            purchasing = self._check_purchasing(day, hour)
            return HourRequest(
                day=day,
                hour=hour,
                flight_loads=[],
                kit_purchasing_orders=purchasing
            )
        
        # Optimize loads and purchases
        result = self.optimizer.optimize_loads_and_purchases(
            flights_to_load=flights_to_load,
            current_inventory=self.inventory,
            day=day,
            hour=hour
        )
        
        # Convert to FlightLoad objects
        flight_loads = []
        for flight in flights_to_load:
            fid_str = str(flight.flight_id)
            if fid_str in result.flight_loads:
                loads = result.flight_loads[fid_str]
                
                # Update our inventory tracking
                self._deduct_from_inventory(
                    flight.origin_airport,
                    loads.first, loads.business,
                    loads.premium_economy, loads.economy
                )
                
                flight_loads.append(FlightLoad(
                    flight_id=flight.flight_id,
                    loaded_kits=loads
                ))
        
        # Apply purchases to inventory tracking (with lead time consideration)
        if result.purchase_amounts.first > 0 or result.purchase_amounts.business > 0 or \
           result.purchase_amounts.premium_economy > 0 or result.purchase_amounts.economy > 0:
            print(f"[PURCHASE] Day{day}:H{hour} - FC={result.purchase_amounts.first}, "
                  f"BC={result.purchase_amounts.business}, PE={result.purchase_amounts.premium_economy}, "
                  f"EC={result.purchase_amounts.economy}")
        
        return HourRequest(
            day=day,
            hour=hour,
            flight_loads=flight_loads,
            kit_purchasing_orders=result.purchase_amounts
        )
    
    def _deduct_from_inventory(self, airport_id: str, fc: int, bc: int, pe: int, ec: int):
        """Deduct loaded kits from inventory."""
        if airport_id in self.inventory:
            self.inventory[airport_id]["fc"] -= fc
            self.inventory[airport_id]["bc"] -= bc
            self.inventory[airport_id]["pe"] -= pe
            self.inventory[airport_id]["ec"] -= ec
    
    def _add_to_inventory(self, airport_id: str, fc: int, bc: int, pe: int, ec: int):
        """Add kits to inventory (when flights land and process)."""
        if airport_id in self.inventory:
            self.inventory[airport_id]["fc"] += fc
            self.inventory[airport_id]["bc"] += bc
            self.inventory[airport_id]["pe"] += pe
            self.inventory[airport_id]["ec"] += ec
    
    def process_landed_flights(self, resp):
        """Process landed flights - add kits back to inventory after simplified delay."""
        from rotables.dto.dto import FlightEventType
        
        for ev in resp.flight_updates:
            if ev.event_type == FlightEventType.LANDED:
                # Simplified: add kits back immediately
                # TODO: Add processing delay queue
                self._add_to_inventory(
                    ev.destination_airport,
                    ev.passengers.first,
                    ev.passengers.business,
                    ev.passengers.premium_economy,
                    ev.passengers.economy
                )
    
    def _check_purchasing(self, day: int, hour: int) -> PerClassAmount:
        """Check if we should purchase (when no flights to load)."""
        if self.optimizer:
            result = self.optimizer._calculate_purchase_needs(
                self.inventory,
                day,
                hour
            )
            return result
        return PerClassAmount(0, 0, 0, 0)
