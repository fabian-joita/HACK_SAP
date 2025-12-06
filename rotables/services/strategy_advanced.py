# rotables/services/strategy_advanced.py

from rotables.dto.dto import HourRequest, FlightLoad, PerClassAmount
from rotables.models.state import GameState
from rotables.models.inventory import Inventory  # probabil există deja; ok dacă e unused


class StrategyAdvanced:
    """
    StrategyAdvanced v4 — UNIVERSAL-STABLE + FORECAST

    Obiective:
    - zero negative inventory (hard safety, inclusiv în remove_stock)
    - zero over-capacity (guard simplu cu slack)
    - folosim zborurile viitoare (GameState.future_flights) pentru forecast
    - HUB1 = sursa principală, dar NU îl golim: păstrăm stock proporțional cu cererea viitoare
    - outstation-urile primesc doar ce își pot permite să piardă fără să-și rupă viitorul
    """

    def __init__(self, state_manager, aircraft_caps):
        self.sm = state_manager
        self.aircraft_caps = aircraft_caps
        self.last_loads = {}

        # pentru informații interne / debugging
        self.current_day = 0
        self.current_hour = 0

    # ===========================================================
    #                    MAIN ENTRY PER ORĂ
    # ===========================================================
    def build_hour_request(self, day: int, hour: int, state: GameState) -> HourRequest:
        self.current_day = day
        self.current_hour = hour

        # 1) procesăm pipeline-ul intern (washing, kitting etc.)
        self.sm.apply_processing(day, hour)

        loads = []

        # 2) luăm zborurile care trebuie încărcate ACUM
        flights_to_load = state.pop_flights_to_load()

        for ev in flights_to_load:
            fl = self.decide_load(ev, state)
            loads.append(fl)
            self.last_loads[ev.flight_id] = fl.loaded_kits

            lk = fl.loaded_kits

            # HARD SAFETY EXTRA la remove_stock:
            #   nu scoatem NICIODATĂ mai mult decât există, chiar dacă
            #   între timp altceva a modificat stocul.
            origin_stock = self.sm.get_stock_inventory(ev.origin_airport)

            safe_fc = min(lk.first, origin_stock.fc)
            safe_bc = min(lk.business, origin_stock.bc)
            safe_pe = min(lk.premium_economy, origin_stock.pe)
            safe_ec = min(lk.economy, origin_stock.ec)

            if safe_fc < 0:
                safe_fc = 0
            if safe_bc < 0:
                safe_bc = 0
            if safe_pe < 0:
                safe_pe = 0
            if safe_ec < 0:
                safe_ec = 0

            self.sm.remove_stock(
                ev.origin_airport,
                safe_fc,
                safe_bc,
                safe_pe,
                safe_ec,
            )

        # 3) cumpărări la HUB
        buying = self.decide_purchasing()

        return HourRequest(
            day=day,
            hour=hour,
            flight_loads=loads,
            kit_purchasing_orders=buying,
        )

    # ===========================================================
    #                 FORECAST CERERE VIITOARE
    # ===========================================================
    def estimate_future_demand(
        self,
        origin_airport: str,
        state: GameState,
        exclude_flight_id=None,
    ) -> PerClassAmount:
        """
        Estimează cererea viitoare (pe toate zborurile programate din acel aeroport),
        folosind GameState.future_flights.

        Nu folosim ore/zile aici (nu știm exact ce câmpuri ai în FlightEvent),
        ci pur și simplu suma PAX pentru toate zborurile viitoare cu același origin.
        """
        demand = PerClassAmount(
            first=0,
            business=0,
            premium_economy=0,
            economy=0,
        )

        # Dacă, din orice motiv, future_flights nu există, fallback pe active_flights
        flights_dict = getattr(state, "future_flights", state.active_flights)

        for fev in flights_dict.values():
            if fev.origin_airport != origin_airport:
                continue
            if exclude_flight_id is not None and fev.flight_id == exclude_flight_id:
                continue

            pax = fev.passengers
            demand.first += pax.first
            demand.business += pax.business
            demand.premium_economy += pax.premium_economy
            demand.economy += pax.economy

        return demand

    # ===========================================================
    #                 UNIVERSAL-STABLE LOADING v4
    # ===========================================================
    def decide_load(self, ev, state: GameState) -> FlightLoad:
        origin = ev.origin_airport
        dest = ev.destination_airport
        pax = ev.passengers
        caps = self.aircraft_caps[ev.aircraft_type]

        st_o = self.sm.get_stock_inventory(origin)
        st_d = self.sm.get_stock_inventory(dest)
        meta_d = self.sm.airports_meta.get(dest)

        # Capacități dest -> fallback mare dacă lipsesc meta-urile
        cap_fc = getattr(meta_d, "capacity_fc", 10**9)
        cap_bc = getattr(meta_d, "capacity_bc", 10**9)
        cap_pe = getattr(meta_d, "capacity_pe", 10**9)
        cap_ec = getattr(meta_d, "capacity_ec", 10**9)

        # ------------------------------------------------------
        # 1) Forecast simplu pe viitor (origin)
        # ------------------------------------------------------
        future = self.estimate_future_demand(
            origin_airport=origin,
            state=state,
            exclude_flight_id=ev.flight_id,
        )

        # ------------------------------------------------------
        # 2) ORIGIN SAFETY (rezervă pentru zborurile viitoare)
        # ------------------------------------------------------
        if origin == "HUB1":
            # HUB1: păstrăm mai mult, e sursa principală
            safe_fc = int(future.first * 1.3)
            safe_bc = int(future.business * 1.3)
            safe_pe = int(future.premium_economy * 1.2)
            safe_ec = int(future.economy * 1.2)
        else:
            # Outstation: păstrăm atât forecast cât și un buffer fix
            base_fc = min(max(3, int(st_o.fc * 0.20)), 50)
            base_bc = min(max(5, int(st_o.bc * 0.20)), 80)
            base_pe = min(max(5, int(st_o.pe * 0.20)), 80)
            base_ec = min(max(40, int(st_o.ec * 0.30)), 300)

            safe_fc = max(base_fc, int(future.first * 1.1))
            safe_bc = max(base_bc, int(future.business * 1.1))
            safe_pe = max(base_pe, int(future.premium_economy * 1.1))
            safe_ec = max(base_ec, int(future.economy * 1.1))

        # nu putem rezerva mai mult decât avem
        safe_fc = min(max(0, safe_fc), st_o.fc)
        safe_bc = min(max(0, safe_bc), st_o.bc)
        safe_pe = min(max(0, safe_pe), st_o.pe)
        safe_ec = min(max(0, safe_ec), st_o.ec)

        # stock disponibil de trimis acum (peste rezervă)
        avail_fc = max(0, st_o.fc - safe_fc)
        avail_bc = max(0, st_o.bc - safe_bc)
        avail_pe = max(0, st_o.pe - safe_pe)
        avail_ec = max(0, st_o.ec - safe_ec)

        # ------------------------------------------------------
        # 3) Base load = min(pax, stock disponibil, capacitate avion)
        # ------------------------------------------------------
        load_fc = min(pax.first, avail_fc, caps["fc"])
        load_bc = min(pax.business, avail_bc, caps["bc"])
        load_pe = min(pax.premium_economy, avail_pe, caps["pe"])
        load_ec = min(pax.economy, avail_ec, caps["ec"])

        # ------------------------------------------------------
        # 4) DESTINATION GUARD – să nu depășim capacitățile dest-ului
        # ------------------------------------------------------
        slack = 30  # margine simplă, universală

        def guard(cur, cap, ld):
            free = cap - cur - slack
            # free poate fi negativ, dar nu trimitem niciodată negativ
            if free <= 0:
                return 0
            return min(ld, free)

        load_fc = guard(st_d.fc, cap_fc, load_fc)
        load_bc = guard(st_d.bc, cap_bc, load_bc)
        load_pe = guard(st_d.pe, cap_pe, load_pe)
        load_ec = guard(st_d.ec, cap_ec, load_ec)

        # ------------------------------------------------------
        # 5) HARD SAFETY: origin NU devine negativ niciodată
        # ------------------------------------------------------
        load_fc = max(0, min(load_fc, st_o.fc))
        load_bc = max(0, min(load_bc, st_o.bc))
        load_pe = max(0, min(load_pe, st_o.pe))
        load_ec = max(0, min(load_ec, st_o.ec))

        # ------------------------------------------------------
        # 6) Construim FlightLoad
        # ------------------------------------------------------
        return FlightLoad(
            ev.flight_id,
            PerClassAmount(
                first=int(load_fc),
                business=int(load_bc),
                premium_economy=int(load_pe),
                economy=int(load_ec),
            ),
        )

    # ===========================================================
    #                 UNIVERSAL-STABLE PURCHASING
    # ===========================================================
    def decide_purchasing(self) -> PerClassAmount:
        hub = "HUB1"
        st = self.sm.get_stock_inventory(hub)
        meta = self.sm.airports_meta.get(hub)

        # capacități HUB1
        cap_fc = getattr(meta, "capacity_fc", 10**9)
        cap_bc = getattr(meta, "capacity_bc", 10**9)
        cap_pe = getattr(meta, "capacity_pe", 10**9)
        cap_ec = getattr(meta, "capacity_ec", 10**9)

        buy_fc = buy_bc = buy_pe = buy_ec = 0

        # ------------------------------------------------------
        # 1) ECO – menținem HUB1 între 30% și 70% din capacitate
        # ------------------------------------------------------
        low_ec = int(cap_ec * 0.30)
        high_ec = int(cap_ec * 0.70)

        if st.ec < low_ec:
            desired = 8000  # cât am vrea să cumpărăm
            free = max(0, high_ec - st.ec)
            buy_ec = min(desired, free)
        else:
            buy_ec = 0

        # hard cap pe oră – universal safe
        buy_ec = min(buy_ec, 8000)

        # ------------------------------------------------------
        # 2) FIRST / BUSINESS / PREMIUM ECO
        # ------------------------------------------------------
        if st.fc < 200:
            buy_fc = min(100, max(0, cap_fc - st.fc - 20))

        if st.bc < 300:
            buy_bc = min(150, max(0, cap_bc - st.bc - 30))

        if st.pe < 400:
            buy_pe = min(150, max(0, cap_pe - st.pe - 30))

        return PerClassAmount(
            first=int(buy_fc),
            business=int(buy_bc),
            premium_economy=int(buy_pe),
            economy=int(buy_ec),
        )