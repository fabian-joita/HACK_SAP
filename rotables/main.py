# rotables/main.py

from rotables.services.api_client import ApiClient
from rotables.services.loader import Loader
from rotables.services.strategy_advanced import StrategyAdvanced
from rotables.services.state_manager import StateManager
from rotables.models.state import GameState
from rotables.dto.dto import HourRequest
from rotables.services.debug_logger import (
    log_request, log_events, log_penalties, log_flight_debug
)


def main():
    print("\n=== ROTABLES ENGINE START ===\n")

    loader = Loader()

    # load configs
    airports = loader.load_airports()
    aircraft_caps = loader.load_aircraft_types()

    sm = StateManager(airports)
    state = GameState()
    state.aircraft_caps = aircraft_caps

    api = ApiClient()
    strategy = StrategyAdvanced(sm, aircraft_caps)

    print("[INFO] Starting or resuming session...")
    api.start_session()

    day, hour = 0, 0

    while True:

        # --------------------------------------------
        # DEBUG: PRINT FULL STOCKS
        # --------------------------------------------
        print("\n==============================")
        print(f"⏰ DEBUG DAY {day} HOUR {hour}")
        print("==============================")

        for ap, st in sm.stock.items():
            print(f"STOCK[{ap}]  FC={st.fc}  BC={st.bc}  PE={st.pe}  EC={st.ec}")

        # --------------------------------------------
        # BUILD REQUEST
        # --------------------------------------------
        req: HourRequest = strategy.build_hour_request(day, hour, state)

        print("\n--- LOAD DECISIONS ---")
        for fl in req.flight_loads:
            print(f"LOAD Flight={fl.flight_id} "
                  f"FC={fl.loaded_kits.first} BC={fl.loaded_kits.business} "
                  f"PE={fl.loaded_kits.premium_economy} EC={fl.loaded_kits.economy}")

        print("\n--- PURCHASING ---")
        print(req.kit_purchasing_orders)

        # --------------------------------------------
        # SEND TO BACKEND
        # --------------------------------------------
        resp = api.play_round(req)

        # state ingest + debug
        state.ingest_response(resp)
        log_events(resp)
        log_penalties(resp)
        log_flight_debug(resp)

        # --------------------------------------------
        # APPLY PURCHASE  *** FIX CRITIC ***
        # --------------------------------------------
        buy = req.kit_purchasing_orders
        if buy.first or buy.business or buy.premium_economy or buy.economy:
            sm.apply_purchase(
                buy.first,
                buy.business,
                buy.premium_economy,
                buy.economy
            )

        # --------------------------------------------
        # APPLY LANDINGS
        # --------------------------------------------
        print("\n--- LANDINGS ---")
        for ev in resp.flight_updates:
            if ev.event_type.value == "LANDED":
                used = strategy.last_loads.get(ev.flight_id)

                if used:
                    sm.apply_landing(
                        airport=ev.destination_airport,
                        used_kits=used,
                        day=resp.day,
                        hour=resp.hour
                    )

                strategy.last_loads.pop(ev.flight_id, None)


        print(f"\n[ROUND] {resp.day}:{resp.hour} cost={resp.total_cost}")

        if resp.day == 29 and resp.hour == 23:
            break

        # advance time
        hour += 1
        if hour == 24:
            hour = 0
            day += 1

    final = api.end_session()
    print("\n=== SIMULATION END ===")
    if final:
        print("FINAL COST:", final.total_cost)
    else:
        print("SESSION CLOSED BY BACKEND")


if __name__ == "__main__":
    main()
