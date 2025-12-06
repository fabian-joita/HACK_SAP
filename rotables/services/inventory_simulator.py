from collections import defaultdict
from rotables.models.inventory import InventoryState
from rotables.models.movement import Movement
# Assuming you have access to Airport model to initialize stock

class InventorySimulator:

    def __init__(self, airports):
        self.airports = airports
        self.inventory = {}
        self.future_movements = []

        # Initialize inventory from Airport data
        for ap_id, ap in airports.items():
            self.inventory[ap_id] = InventoryState(
                fc=ap.initial_fc_stock,
                bc=ap.initial_bc_stock,
                pe=ap.initial_pe_stock,
                ec=ap.initial_ec_stock,
            )

    def schedule_movement(self, day, hour, airport_id, cabin_class, qty):
        # Kits loaded onto a plane are considered "moved" to the destination (where they are processed/returned)
        self.future_movements.append(Movement(day, hour, airport_id, cabin_class, qty))

    def apply_movements(self, day, hour):
        # This method would process returns/arrivals (Movement.delta > 0)
        remaining = []
        for mv in self.future_movements:
            if mv.day == day and mv.hour == hour:
                st = self.inventory[mv.airport_id]
                # Logic to apply stock changes (as per your original code)
                # ...
            else:
                remaining.append(mv)
        self.future_movements = remaining