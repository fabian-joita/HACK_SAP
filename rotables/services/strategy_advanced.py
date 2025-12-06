# rotables/services/strategy_advanced.py

from rotables.dto.dto import HourRequest, FlightLoad, PerClassAmount
from rotables.models.state import GameState


class StrategyAdvanced:
    """
    Strategie HYBRID (B + C):

    - Încărcare (decide_load):
        * identic ca Strategy B: încercăm 1 kit / pasager,
          limitați de stoc + capacitate avion.
        * funcționează bine atât HUB1→A, cât și A→HUB1.

    - Cumpărare (decide_purchasing):
        * doar în HUB1;
        * 3 zone:
            - UNDERSTOCK  → cumpărăm mult (ca înainte);
            - LOW STOCK   → cumpărăm mai puțin (top-up);
            - OVERSTOCK   → nu cumpărăm nimic.
    """

    def __init__(self, state_manager, aircraft_caps):
        self.sm = state_manager
        self.aircraft_caps = aircraft_caps

        # flight_id -> PerClassAmount încărcat la decolare
        self.last_loads = {}

    # ===========================================================
    def build_hour_request(self, day: int, hour: int, state: GameState) -> HourRequest:
        """
        Este apelată la fiecare oră din main():
          1. aplicăm procesările care s-au terminat;
          2. preluăm zborurile care trebuie încărcate în această oră;
          3. decidem câte kituri încărcăm pe fiecare zbor;
          4. decidem ce cumpărăm în HUB1;
          5. construim HourRequest pentru backend.
        """

        # 1. eliberăm kituri procesate care au ajuns la maturitate
        self.sm.apply_processing(day, hour)

        # 2. zboruri de încărcat în această oră
        loads = []
        flights = state.pop_flights_to_load()

        for ev in flights:
            # 3. decizie de încărcare
            fl = self.decide_load(ev)
            loads.append(fl)

            # memorăm câte kituri am încărcat pe acest flight_id
            self.last_loads[ev.flight_id] = fl.loaded_kits

            # scădem din stocul aeroportului de origine
            lk = fl.loaded_kits
            self.sm.remove_stock(
                ev.origin_airport,
                lk.first,
                lk.business,
                lk.premium_economy,
                lk.economy,
            )

        # 4. decizie de cumpărare (doar HUB1, politică hybrid)
        buying = self.decide_purchasing()

        # 5. construim request-ul pentru API
        return HourRequest(
            day=day,
            hour=hour,
            flight_loads=loads,
            kit_purchasing_orders=buying,
        )

    # ===========================================================
    # LOADING – baza Strategy B (stabilă)
    # ===========================================================
    def decide_load(self, ev) -> FlightLoad:
        origin = ev.origin_airport
        dest   = ev.destination_airport
        pax    = ev.passengers
        air_type = ev.aircraft_type

        caps = self.aircraft_caps[air_type]
        st   = self.sm.get_stock_inventory(origin)

        # ==============================
        # 1) IDEAL KITS (1 per pax)
        # ==============================
        ideal_fc = pax.first
        ideal_bc = pax.business
        ideal_pe = pax.premium_economy
        ideal_ec = pax.economy

        # ==============================
        # 2) DISPONIBIL (safe) în aeroport
        # ==============================
        if origin == "HUB1":
            avail_fc = st.fc
            avail_bc = st.bc
            avail_pe = st.pe
            avail_ec = st.ec
        else:
            # buffer pentru aeroporturi mici
            avail_fc = max(0, st.fc - max(5, int(st.fc * 0.30)))
            avail_bc = max(0, st.bc - max(5, int(st.bc * 0.30)))
            avail_pe = max(0, st.pe - max(5, int(st.pe * 0.30)))
            avail_ec = max(0, st.ec - max(40, int(st.ec * 0.50)))

        # ==============================
        # 3) LOAD de bază (limitări avion + safe stock)
        # ==============================
        load_fc = min(ideal_fc, avail_fc, caps["fc"])
        load_bc = min(ideal_bc, avail_bc, caps["bc"])
        load_pe = min(ideal_pe, avail_pe, caps["pe"])
        load_ec = min(ideal_ec, avail_ec, caps["ec"])

        # ==============================
        # 4) EXCEPȚIE: ZBOR CĂTRE HUB1 → MAXIM ECONOMY
        # ==============================
        if dest == "HUB1":
            load_ec = min(st.ec, caps["ec"])

        # ==============================
        # 5) PROTECȚIE INVENTORY_EXCEEDS_CAPACITY
        # ==============================
        dest_meta = self.sm.airports_meta[dest]
        dest_st   = self.sm.get_stock_inventory(dest)

        # nu depășim capacitatea aeroportului
        load_fc = min(load_fc, max(0, dest_meta.capacity_fc - dest_st.fc))
        load_bc = min(load_bc, max(0, dest_meta.capacity_bc - dest_st.bc))
        load_pe = min(load_pe, max(0, dest_meta.capacity_pe - dest_st.pe))
        load_ec = min(load_ec, max(0, dest_meta.capacity_ec - dest_st.ec))

        # ==============================
        # 6) CREĂM kits FINAL (după ajustări!)
        # ==============================
        kits = PerClassAmount(
            first=load_fc,
            business=load_bc,
            premium_economy=load_pe,
            economy=load_ec,
        )

        return FlightLoad(
            flight_id=ev.flight_id,
            loaded_kits=kits,
        )

    # ===========================================================
    # PURCHASING – HYBRID (B + C)
    # ===========================================================
    def decide_purchasing(self) -> PerClassAmount:
        """
        Politică de cumpărare HYBRID în HUB1:

        - UNDERSTOCK (foarte jos) → cumpărăm mult (ca în varianta simplă);
        - LOW STOCK (un pic sub confort) → cumpărăm mai puțin (top-up);
        - OVERSTOCK (stoc mare, > ~3 zile) → nu cumpărăm nimic.

        Doar HUB1 poate cumpăra.
        """
        hub = "HUB1"
        st = self.sm.get_stock_inventory(hub)

        # Praguri de referință (aprox. “minim confortabil”)
        min_fc, min_bc, min_pe, min_ec = 300, 600, 800, 12_000

        # “zona de mijloc” (între OK și overstock)
        mid_fc, mid_bc, mid_pe, mid_ec = 600, 1_200, 1_600, 20_000

        # peste asta considerăm overstock (nu mai cumpărăm)
        max_fc, max_bc, max_pe, max_ec = 3 * min_fc, 3 * min_bc, 3 * min_pe, 3 * min_ec

        buy_fc = buy_bc = buy_pe = buy_ec = 0

        # ---------- FIRST ----------
        if st.fc < min_fc:
            # foarte puțin → refill serios
            buy_fc = 200
        elif st.fc < mid_fc:
            # un pic cam jos → top-up mic
            buy_fc = 100

        # ---------- BUSINESS ----------
        if st.bc < min_bc:
            buy_bc = 300
        elif st.bc < mid_bc:
            buy_bc = 150

        # ---------- PREMIUM ECO ----------
        if st.pe < min_pe:
            buy_pe = 300
        elif st.pe < mid_pe:
            buy_pe = 150

        # ---------- ECONOMY ----------
        if st.ec < min_ec:
            buy_ec = 2_000
        elif st.ec < mid_ec:
            buy_ec = 1_000

        # ---------- OVERSTOCK GUARD ----------
        if st.fc > max_fc:
            buy_fc = 0
        if st.bc > max_bc:
            buy_bc = 0
        if st.pe > max_pe:
            buy_pe = 0
        if st.ec > max_ec:
            buy_ec = 0

        return PerClassAmount(
            first=buy_fc,
            business=buy_bc,
            premium_economy=buy_pe,
            economy=buy_ec,
        )
