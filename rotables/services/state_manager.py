# rotables/services/state_manager.py

from dataclasses import dataclass
from collections import defaultdict

from rotables.models.inventory import Inventory
from rotables.models.airport import Airport
from rotables.dto.dto import PerClassAmount


@dataclass
class ProcessingItem:
    kit_type: str
    qty: int
    ready_day: int
    ready_hour: int


class StateManager:

    def __init__(self, airports):
        # airport metadata by code
        self.airports_meta = {ap.code: ap for ap in airports}

        # real stock inventories (start with initial stock!)
        self.stock = {
            ap.code: Inventory(
                fc=ap.initial_fc_stock,
                bc=ap.initial_bc_stock,
                pe=ap.initial_pe_stock,
                ec=ap.initial_ec_stock,
            )
            for ap in airports
        }

        # processing queues
        self.processing = defaultdict(list)

    # ----------------------------------------------------------
    # GET STOCK
    # ----------------------------------------------------------
    def get_stock_inventory(self, airport_code: str) -> Inventory:
        return self.stock[airport_code]

    # ----------------------------------------------------------
    # REMOVE STOCK (loading into plane)
    # ----------------------------------------------------------
    def remove_stock(self, airport, fc, bc, pe, ec):
        st = self.stock[airport]

        # Protecție: nu permitem niciodată negative
        fc = min(fc, st.fc)
        bc = min(bc, st.bc)
        pe = min(pe, st.pe)
        ec = min(ec, st.ec)

        st.fc -= fc
        st.bc -= bc
        st.pe -= pe
        st.ec -= ec

    # ----------------------------------------------------------
    # ADD STOCK
    # ----------------------------------------------------------
    def add_stock(self, airport: str, fc: int, bc: int, pe: int, ec: int):
        st = self.stock[airport]
        st.fc += fc
        st.bc += bc
        st.pe += pe
        st.ec += ec

    # ----------------------------------------------------------
    # APPLY PURCHASE (ALWAYS TO HUB1)
    # ----------------------------------------------------------
    def apply_purchase(self, fc: int, bc: int, pe: int, ec: int):
        hub = "HUB1"
        self.add_stock(hub, fc, bc, pe, ec)

    # ----------------------------------------------------------
    # INTERNAL: ready time calculator
    # ----------------------------------------------------------
    def _ready_time(self, day, hour, extra):
        total = day * 24 + hour + extra
        return total // 24, total % 24

    # ----------------------------------------------------------
    # APPLY LANDING (kits go to processing)
    # ----------------------------------------------------------
    def apply_landing(self, airport, used_kits: PerClassAmount, day, hour):

        ap_meta: Airport = self.airports_meta[airport]

        # create processing tasks for each kit class
        if used_kits.first > 0:
            rd, rh = self._ready_time(day, hour, ap_meta.first_processing_time)
            self.processing[airport].append(
                ProcessingItem("fc", used_kits.first, rd, rh)
            )

        if used_kits.business > 0:
            rd, rh = self._ready_time(day, hour, ap_meta.business_processing_time)
            self.processing[airport].append(
                ProcessingItem("bc", used_kits.business, rd, rh)
            )

        if used_kits.premium_economy > 0:
            rd, rh = self._ready_time(day, hour, ap_meta.premium_economy_processing_time)
            self.processing[airport].append(
                ProcessingItem("pe", used_kits.premium_economy, rd, rh)
            )

        if used_kits.economy > 0:
            rd, rh = self._ready_time(day, hour, ap_meta.economy_processing_time)
            self.processing[airport].append(
                ProcessingItem("ec", used_kits.economy, rd, rh)
            )

    # ----------------------------------------------------------
    # RELEASE PROCESSED KITS
    # ----------------------------------------------------------
    def apply_processing(self, day, hour):

        for ap, q in self.processing.items():
            new_q = []

            for item in q:
                if (day > item.ready_day) or (day == item.ready_day and hour >= item.ready_hour):
                    # return to usable stock
                    if item.kit_type == "fc":
                        self.stock[ap].fc += item.qty
                    elif item.kit_type == "bc":
                        self.stock[ap].bc += item.qty
                    elif item.kit_type == "pe":
                        self.stock[ap].pe += item.qty
                    elif item.kit_type == "ec":
                        self.stock[ap].ec += item.qty
                else:
                    new_q.append(item)

            self.processing[ap] = new_q
