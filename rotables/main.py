from rotables.services.api_client import ApiClient
from rotables.services.loader import Loader
from rotables.services.strategy_advanced import StrategyAdvanced
from rotables.services.state_manager import StateManager
from rotables.models.state import GameState
from rotables.dto.dto import HourRequest
from rotables.services.debug_logger import (
    log_request, log_events, log_penalties, log_flight_debug
)
from datetime import datetime

# ======================================================
# FILE LOGGER
# ======================================================
LOG_FILE = "rotables/logs/debug_output.txt"

def log_to_file(text: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def debug_print(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    print(msg)
    log_to_file(msg)


def main():
    debug_print("\n=== ROTABLES ENGINE START ===\n")

    loader = Loader()

    # load configs
    airports = loader.load_airports()
    aircraft_caps = loader.load_aircraft_types()

    sm = StateManager(airports)
    state = GameState()
    state.aircraft_caps = aircraft_caps

    api = ApiClient()
    strategy = StrategyAdvanced(sm, aircraft_caps)

    debug_print("[INFO] Starting or resuming session...")
    api.start_session()

    day, hour = 0, 0
    daily_costs = []

    while True:
        req: HourRequest = strategy.build_hour_request(day, hour, state)
        resp = api.play_round(req)

        state.ingest_response(resp)
        log_events(resp)
        log_penalties(resp)
        log_flight_debug(resp)

        buy = req.kit_purchasing_orders
        if buy.first or buy.business or buy.premium_economy or buy.economy:
            sm.apply_purchase(
                buy.first,
                buy.business,
                buy.premium_economy,
                buy.economy
            )

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

        # --- Hourly cost ---
        debug_print(f"[ROUND] {resp.day}:{resp.hour} cost={resp.total_cost}")
        daily_costs.append(resp.total_cost)

        # --- Hourly stock snapshot per airport ---
        stock_snapshot = ", ".join(
            f"{ap}=FC:{st.fc} BC:{st.bc} PE:{st.pe} EC:{st.ec}"
            for ap, st in sm.stock.items()
        )
        debug_print(f"[STOCKS] {resp.day}:{resp.hour} {stock_snapshot}")

        # --- End of day summary ---
        if resp.hour == 23:
            day_total = sum(daily_costs)
            day_avg = day_total / len(daily_costs)
            end_of_day_cost = daily_costs[-1]
            debug_print(f"[DAY] {resp.day} totalCost={day_total:.2f} avgCost={day_avg:.2f} endOfDayCost={end_of_day_cost:.2f}")
            daily_costs = []  # reset for next day

        # increment time
        hour += 1
        if hour == 24:
            hour = 0
            day += 1
            if day > 29:
                break

    debug_print("\n=== SIMULATION END ===")
    debug_print("SESSION CLOSED BY BACKEND")

if __name__ == "__main__":
    main()