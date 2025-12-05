from models.inventory import InventoryState
from models.movement import Movement

class InventorySimulator:

    def __init__(self, airports):
        self.airports = airports
        self.inventory = {}
        self.future_movements = []

        for ap_id, ap in airports.items():
            self.inventory[ap_id] = InventoryState(
                fc=ap.initial_fc_stock,
                bc=ap.initial_bc_stock,
                pe=ap.initial_pe_stock,
                ec=ap.initial_ec_stock,
            )

    def schedule_movement(self, day, hour, airport_id, cabin_class, qty):
        self.future_movements.append(Movement(day, hour, airport_id, cabin_class, qty))

    def apply_movements(self, day, hour):
        remaining = []
        for mv in self.future_movements:
            if mv.day == day and mv.hour == hour:
                st = self.inventory[mv.airport_id]
                if mv.cabin_class == "FIRST":
                    st.fc += mv.delta
                elif mv.cabin_class == "BUSINESS":
                    st.bc += mv.delta
                elif mv.cabin_class == "PREMIUM_ECONOMY":
                    st.pe += mv.delta
                else:
                    st.ec += mv.delta
            else:
                remaining.append(mv)

        self.future_movements = remaining
