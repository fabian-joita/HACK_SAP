from rotables.dto.dto import HourRequest, FlightLoad, PerClassAmount
from rotables.models.state import GameState


class StrategyAdvanced:
    """
    Strategie simplă, dar robustă, pentru Hub-and-Spoke:

    - cumpărăm kituri DOAR în HUB1;
    - la încărcare, nu depășim:
        * capacitatea avionului
        * stocul disponibil în aeroport
        * numărul de pasageri pe clasă;
    - ținem minte câte kituri am încărcat pe fiecare zbor în last_loads,
      ca să putem procesa corect la aterizare.
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

        # 4. decizie de cumpărare (doar HUB1)
        buying = self.decide_purchasing()

        # 5. construim request-ul pentru API
        return HourRequest(
            day=day,
            hour=hour,
            flight_loads=loads,
            kit_purchasing_orders=buying,
        )

    # ===========================================================
    def decide_load(self, ev) -> FlightLoad:
        """
        Decide câte kituri încărcăm pentru un singur zbor.

        Regula este aceeași și pentru HUB1→A și A→HUB1:
        - vrem ca FIECARE pasager să aibă un kit (dacă avem stoc suficient);
        - nu putem depăși nici capacitatea avionului, nici stocul.
        """

        origin = ev.origin_airport
        pax = ev.passengers
        air_type = ev.aircraft_type

        caps = self.aircraft_caps[air_type]
        st = self.sm.get_stock_inventory(origin)

        # ideal = câte kituri ne-ar trebui ca fiecare pasager să aibă unul
        ideal_fc = pax.first
        ideal_bc = pax.business
        ideal_pe = pax.premium_economy
        ideal_ec = pax.economy

        # nu putem depăși stocul și nici capacitatea avionului
        load_fc = min(st.fc, ideal_fc, caps["fc"])
        load_bc = min(st.bc, ideal_bc, caps["bc"])
        load_pe = min(st.pe, ideal_pe, caps["pe"])
        load_ec = min(st.ec, ideal_ec, caps["ec"])

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
    def decide_purchasing(self) -> PerClassAmount:
        """
        Politică simplă de cumpărare în HUB1 pentru a evita rămânerea fără kituri.

        Ideea:
        - dacă stocul scade sub un prag, facem o comandă "grăsuță";
        - altfel nu cumpărăm nimic (0).
        Pragurile și cantitățile sunt empirice și pot fi ajustate.
        """
        hub = "HUB1"
        st = self.sm.get_stock_inventory(hub)

        # limite sigure & economice (pot fi tweak-uite)
        buy_fc = 200 if st.fc < 300 else 0
        buy_bc = 300 if st.bc < 600 else 0
        buy_pe = 300 if st.pe < 800 else 0
        buy_ec = 2000 if st.ec < 12_000 else 0

        return PerClassAmount(
            first=buy_fc,
            business=buy_bc,
            premium_economy=buy_pe,
            economy=buy_ec,
        )
