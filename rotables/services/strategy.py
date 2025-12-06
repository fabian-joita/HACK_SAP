import math
from typing import List
from rotables.dto.dto import HourRequest, FlightLoad, PerClassAmount, FlightEvent
from rotables.models.state import GameState
from rotables.services.debug_logger import log_debug
# Assuming Planner and InventorySimulator are available in the scope
# of this file, or are imported here if needed (e.g., from rotables.services.planner import Planner)


class Strategy:
    
    # ASSUMES: planner and inventory_simulator are passed in rotables/main.py
    def __init__(self, planner, inventory_simulator):
        self.planner = planner
        self.inventory_simulator = inventory_simulator

    def build_hour_request(self, day: int, hour: int, state: GameState) -> HourRequest:

        flights_to_load = state.pop_flights_to_load()
        flight_loads: List[FlightLoad] = []

        for ev in flights_to_load:

            # debug AB1105
            if ev.flight_number == "AB1105":
                log_debug(day, hour, "STRATEGY", "CHECKED_IN", ev,
                          fc=ev.passengers.first,
                          bc=ev.passengers.business,
                          pe=ev.passengers.premium_economy,
                          ec=ev.passengers.economy,
                          note="Strategy sees flight to load")

            fl = self._decide_load(ev, day, hour) # Pass day and hour for scheduling
            flight_loads.append(fl)

        # --- 3. Kit Purchasing Logic ---
        total_purchase = {"fc": 0, "bc": 0, "pe": 0, "ec": 0}

        for airport_id, stock in self.inventory_simulator.inventory.items():
            target = self.planner.target_stock(airport_id)
            
            # Calculate deficit (need to purchase)
            fc_buy = max(0, target["fc"] - stock.fc)
            bc_buy = max(0, target["bc"] - stock.bc)
            pe_buy = max(0, target["pe"] - stock.pe)
            ec_buy = max(0, target["ec"] - stock.ec)

            # Aggregate total purchase order
            total_purchase["fc"] += fc_buy
            total_purchase["bc"] += bc_buy
            total_purchase["pe"] += pe_buy
            total_purchase["ec"] += ec_buy

        purchasing = PerClassAmount(
            first=total_purchase["fc"],
            business=total_purchase["bc"],
            premium_economy=total_purchase["pe"],
            economy=total_purchase["ec"]
        )

        return HourRequest(
            day=day,
            hour=hour,
            flight_loads=flight_loads,
            kit_purchasing_orders=purchasing
        )

    # ---------------------------------------------------------------------
    # 2. ADVANCED ALLOCATION
    # ---------------------------------------------------------------------
    def _decide_load(self, ev: FlightEvent, current_day: int, current_hour: int) -> FlightLoad:
        
        # 1. LOOKUP STATIC DATA
        # We cast to str just to be safe, as UUIDs sometimes behave oddly in dict lookups
        flight_instance = self.planner.state.flight_schedule.get(str(ev.flight_id))
        
        if not flight_instance:
            # Fallback if the flight isn't in our loaded schedule
            return FlightLoad(ev.flight_id, PerClassAmount(0,0,0,0))

        # --- FIX: Use correct attribute names here ---
        origin_airport_id = flight_instance.origin_airport_id
        destination_airport_id = flight_instance.destination_airport_id
        # ---------------------------------------------
        
        # Get Stock at Origin
        current_stock = self.inventory_simulator.inventory.get(origin_airport_id)
        if not current_stock:
             return FlightLoad(ev.flight_id, PerClassAmount(0,0,0,0))

        # --- Constants & Setup ---
        PASSENGERS_PER_KIT_PLANNED = 20
        PASSENGERS_PER_KIT_ACTUAL = 1
        PLANNED_BUFFER_FACTOR = 0.8
        
        loaded_kits_dict = {}
        classes = ["fc", "bc", "pe", "ec"]
        
        # Map class codes to simulator cabin strings
        class_map = {
            "fc": "FIRST", 
            "bc": "BUSINESS", 
            "pe": "PREMIUM_ECONOMY", 
            "ec": "ECONOMY"
        }
        
        for class_name in classes:
            # Planned: from flight_instance (loaded from CSV)
            planned_pax = flight_instance.passengers_planned.get(class_name, 0)
            
            # Actual: from the Event (ev)
            if class_name == "fc": actual_pax = ev.passengers.first
            elif class_name == "bc": actual_pax = ev.passengers.business
            elif class_name == "pe": actual_pax = ev.passengers.premium_economy
            else: actual_pax = ev.passengers.economy

            # 2. CALCULATION (80% planned rule + Actuals)
            base_kits_planned = (int(planned_pax * PLANNED_BUFFER_FACTOR) + PASSENGERS_PER_KIT_PLANNED - 1) // PASSENGERS_PER_KIT_PLANNED
            required = max(base_kits_planned, actual_pax // PASSENGERS_PER_KIT_ACTUAL)
            
            # 3. STOCK CONSTRAINT
            stock_val = getattr(current_stock, class_name)
            load = min(required, stock_val)

            # --- ADD THIS DEBUG PRINT ---
            if required > stock_val:
                print(f"[SHORTAGE] Flight: {ev.flight_number}, Airport: {origin_airport_id}, Class: {class_name}")
                print(f"--- Required: {required} vs Stock: {stock_val}. Loaded: {load}")
            # -----------------------------

            loaded_kits_dict[class_name] = load

            # 4. UPDATE STOCK & SCHEDULE RETURN
            if load > 0:
                # Remove from origin
                current_stock.remove(**{class_name: load})
                
                # Schedule arrival at destination (kits return clean)
                self.inventory_simulator.schedule_movement(
                    ev.arr_day, ev.arr_hour, 
                    destination_airport_id,  # <--- Use the fixed variable
                    class_map[class_name], 
                    load
                )

        return FlightLoad(
            flight_id=ev.flight_id,
            loaded_kits=PerClassAmount(
                loaded_kits_dict["fc"], loaded_kits_dict["bc"], 
                loaded_kits_dict["pe"], loaded_kits_dict["ec"]
            )
        )