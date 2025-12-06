# rotables/services/strategy_advanced.py

from rotables.dto.dto import HourRequest, FlightLoad, PerClassAmount
from rotables.models.state import GameState


class StrategyAdvanced:
    """
    Strategie D – HYBRID + Protecție Capacitate

    - LOADING (decide_load):
        * bazat pe Strategy B (1 kit / pasager, limitat de stoc + avion);
        * pe aeroporturi NON-HUB1 folosim doar o parte din stoc (buffer);
        * înainte să încărcăm, verificăm și capacitatea aeroportului de destinație
          ca să evităm INVENTORY_EXCEEDS_CAPACITY.

    - PURCHASING (decide_purchasing):
        * doar în HUB1;
        * 3 zone (UNDERSTOCK / LOW STOCK / OVERSTOCK);
        * suplimentar: nu cumpără peste ce încape fizic în HUB1,
          ținând un mic headroom (10–15%).
    """

    def __init__(self, state_manager, aircraft_caps):
        self.sm = state_manager
        self.aircraft_caps = aircraft_caps

        # flight_id -> PerClassAmount încărcat la decolare (dacă vrei debugging ulterior)
        self.last_loads = {}

    # ===========================================================
    # MAIN ENTRY – se apelează din main.py la fiecare oră
    # ===========================================================
    def build_hour_request(self, day: int, hour: int, state: GameState) -> HourRequest:
        """
        La fiecare oră:
          1. aplicăm procesările care s-au terminat;
          2. aflăm zborurile care pleacă acum;
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

            # 3b. scădem din stocul aeroportului de origine
            lk = fl.loaded_kits
            self.sm.remove_stock(
                ev.origin_airport,
                lk.first,
                lk.business,
                lk.premium_economy,
                lk.economy,
            )

        # 4. decizie de cumpărare (doar HUB1, politică Strategy D)
        buying = self.decide_purchasing()

        # 5. construim request-ul pentru API
        return HourRequest(
            day=day,
            hour=hour,
            flight_loads=loads,
            kit_purchasing_orders=buying,
        )

    # ===========================================================
    # LOADING – Strategy D
    # ===========================================================
    def decide_load(self, ev) -> FlightLoad:
        """
        Decide câte kituri încărcăm pentru un singur zbor.

        Reguli:
        - vrem 1 kit / pasager (dacă avem stoc);
        - nu depășim capacitatea avionului;
        - nu consumăm tot stocul pe aeroporturile NON-HUB1 (buffer local);
        - nu trimitem către destinație mai mult decât poate încăpea
          (aprox.) în capacitatea aeroportului destinație.
        """

        origin = ev.origin_airport
        dest = ev.destination_airport
        pax = ev.passengers
        air_type = ev.aircraft_type

        caps_plane = self.aircraft_caps[air_type]
        st_origin = self.sm.get_stock_inventory(origin)

        # ideal = câte kituri ne-ar trebui ca fiecare pasager să aibă unul
        ideal_fc = pax.first
        ideal_bc = pax.business
        ideal_pe = pax.premium_economy
        ideal_ec = pax.economy

        # ---------------------------------------------------------
        # 1) Stoc disponibil la ORIGIN (cu buffer pe aeroporturi NON-HUB1)
        # ---------------------------------------------------------
        if origin == "HUB1":
            # În HUB1 putem folosi practic tot ce vedem
            avail_fc = st_origin.fc
            avail_bc = st_origin.bc
            avail_pe = st_origin.pe
            avail_ec = st_origin.ec
        else:
            # Aeroport secundar:
            #  - păstrăm o rezervă serioasă ca să nu golim aeroportul
            #  - valorile sunt un compromis între a ajuta pasagerii
            #    și a nu crea NEGATIVE_INVENTORY în backend.
            buffer_fc = max(5, int(st_origin.fc * 0.30))   # păstrăm ~30% sau min 5
            buffer_bc = max(5, int(st_origin.bc * 0.30))
            buffer_pe = max(5, int(st_origin.pe * 0.30))
            buffer_ec = max(40, int(st_origin.ec * 0.50))  # păstrăm ~50% sau min 40

            avail_fc = max(0, st_origin.fc - buffer_fc)
            avail_bc = max(0, st_origin.bc - buffer_bc)
            avail_pe = max(0, st_origin.pe - buffer_pe)
            avail_ec = max(0, st_origin.ec - buffer_ec)

        # ---------------------------------------------------------
        # 2) Load inițial – limitat de pasageri + avion + stoc disponibil
        # ---------------------------------------------------------
        base_fc = min(avail_fc, ideal_fc, caps_plane["fc"])
        base_bc = min(avail_bc, ideal_bc, caps_plane["bc"])
        base_pe = min(avail_pe, ideal_pe, caps_plane["pe"])
        base_ec = min(avail_ec, ideal_ec, caps_plane["ec"])

        # ---------------------------------------------------------
        # 3) Protecție INVENTORY_EXCEEDS_CAPACITY la DESTINAȚIE
        # ---------------------------------------------------------
        load_fc = base_fc
        load_bc = base_bc
        load_pe = base_pe
        load_ec = base_ec

        dest_meta = self.sm.airports_meta.get(dest)
        if dest_meta is not None:
            # Capacitate reală a aeroportului destinație
            cap_fc = getattr(dest_meta, "capacity_fc", None)
            cap_bc = getattr(dest_meta, "capacity_bc", None)
            cap_pe = getattr(dest_meta, "capacity_pe", None)
            cap_ec = getattr(dest_meta, "capacity_ec", None)

            st_dest = self.sm.get_stock_inventory(dest)

            # Lăsăm un headroom (10–15%) ca să nu umplem exact la limită,
            # fiindcă mai pot veni și alte zboruri în același hour.
            headroom_ratio = 0.20

            def safe_room(cap, current):
                if cap is None:
                    return 10**9  # fallback foarte mare dacă lipsesc date
                max_allowed = int(cap * (1.0 - headroom_ratio))
                return max(0, max_allowed - current)

            room_fc = safe_room(cap_fc, st_dest.fc)
            room_bc = safe_room(cap_bc, st_dest.bc)
            room_pe = safe_room(cap_pe, st_dest.pe)
            room_ec = safe_room(cap_ec, st_dest.ec)

            # Ajustăm încărcarea să nu depășească spațiul "safe" de la destinație
            load_fc = min(load_fc, room_fc)
            load_bc = min(load_bc, room_bc)
            load_pe = min(load_pe, room_pe)
            load_ec = min(load_ec, room_ec)

        # ---------------------------------------------------------
        # 4) Construim obiectul PerClassAmount cu valorile finale
        # ---------------------------------------------------------
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
    # PURCHASING – Strategy D (HUB1 only)
    # ===========================================================
    def decide_purchasing(self) -> PerClassAmount:
        """
        Politică de cumpărare HYBRID în HUB1 (Strategy D):

        - UNDERSTOCK (foarte jos) → cumpărăm mai mult;
        - LOW STOCK (un pic sub confort) → cumpărăm mai puțin (top-up);
        - OVERSTOCK → nu cumpărăm nimic;
        - În plus: nu cumpărăm peste ce încape în capacitatea HUB1,
          păstrând un mic headroom de siguranță.
        """

        hub = "HUB1"
        st = self.sm.get_stock_inventory(hub)
        hub_meta = self.sm.airports_meta.get(hub, None)

        # Praguri de referință (aprox. “minim confortabil”)
        min_fc, min_bc, min_pe, min_ec = 300, 600, 800, 12_000

        # “zona de mijloc” (între OK și overstock moderat)
        mid_fc, mid_bc, mid_pe, mid_ec = 600, 1_200, 1_600, 20_000

        # Limite peste care considerăm overstock serios
        max_fc, max_bc, max_pe, max_ec = 3 * min_fc, 3 * min_bc, 3 * min_pe, 3 * min_ec

        buy_fc = buy_bc = buy_pe = buy_ec = 0

        # ---------- FIRST ----------
        if st.fc < min_fc:
            buy_fc = 150  # ușor redus față de varianta foarte agresivă
        elif st.fc < mid_fc:
            buy_fc = 80

        # ---------- BUSINESS ----------
        if st.bc < min_bc:
            buy_bc = 250
        elif st.bc < mid_bc:
            buy_bc = 120

        # ---------- PREMIUM ECO ----------
        if st.pe < min_pe:
            buy_pe = 250
        elif st.pe < mid_pe:
            buy_pe = 120

        # ---------- ECONOMY ----------
        if st.ec < min_ec:
            buy_ec = 1_800
        elif st.ec < mid_ec:
            buy_ec = 900

        # ---------- OVERSTOCK GUARD (logică de nivel) ----------
        if st.fc > max_fc:
            buy_fc = 0
        if st.bc > max_bc:
            buy_bc = 0
        if st.pe > max_pe:
            buy_pe = 0
        if st.ec > max_ec:
            buy_ec = 0

        # ---------- CAPACITY-AWARE GUARD pentru HUB1 ----------
        if hub_meta is not None:
            cap_fc = getattr(hub_meta, "capacity_fc", None)
            cap_bc = getattr(hub_meta, "capacity_bc", None)
            cap_pe = getattr(hub_meta, "capacity_pe", None)
            cap_ec = getattr(hub_meta, "capacity_ec", None)

            # Lăsăm 10% spațiu liber în HUB1
            headroom_ratio = 0.10

            def clamp_to_capacity(cap, current, planned):
                if cap is None:
                    return planned
                max_allowed = int(cap * (1.0 - headroom_ratio))
                free_space = max(0, max_allowed - current)
                return max(0, min(planned, free_space))

            buy_fc = clamp_to_capacity(cap_fc, st.fc, buy_fc)
            buy_bc = clamp_to_capacity(cap_bc, st.bc, buy_bc)
            buy_pe = clamp_to_capacity(cap_pe, st.pe, buy_pe)
            buy_ec = clamp_to_capacity(cap_ec, st.ec, buy_ec)

        # ---------- Hard cap global pe ora curentă (să nu explodeze costul) ----------
        # Mai ales pe economy.
        max_ec_per_hour = 4_000
        if buy_ec > max_ec_per_hour:
            buy_ec = max_ec_per_hour

        return PerClassAmount(
            first=buy_fc,
            business=buy_bc,
            premium_economy=buy_pe,
            economy=buy_ec,
        )
