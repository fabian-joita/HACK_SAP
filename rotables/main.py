from pathlib import Path

from rotables.services.api_client import ApiClient
from rotables.services.loader import Loader
from rotables.services.strategy_advanced import StrategyAdvanced
from rotables.services.state_manager import StateManager
from rotables.models.state import GameState
from rotables.dto.dto import HourRequest, PerClassAmount
from rotables.services.debug_logger import (
    log_events,
    log_penalties,
    log_flight_debug,
)

# ======================================================
# FILE LOGGER (robust)
# ======================================================
LOG_FILE = Path("rotables/logs/debug_output.txt")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def log_to_file(text: str) -> None:
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception:
        # Nu stricăm simularea dacă logging-ul eșuează.
        pass


def debug_print(*args) -> None:
    msg = " ".join(str(a) for a in args)
    print(msg)
    log_to_file(msg)


# ======================================================
# MAIN — PIPELINE FIXED
# ======================================================
def main() -> None:
    debug_print("\n=== ROTABLES ENGINE START ===\n")

    # --------------------------
    # LOAD STATIC DATA
    # --------------------------
    loader = Loader()
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

    prev_total_cost: float = 0.0
    daily_costs: list[float] = []

    while True:
        debug_print(f"\n⏰ {day}:{hour}")

        # ==========================
        # BUILD REQUEST
        # ==========================
        req: HourRequest = strategy.build_hour_request(day, hour, state)

        # ==========================
        # PLAY ROUND
        # ==========================
        resp = api.play_round(req)

        # Debug backend (penalties & zboruri)
        log_events(resp)
        log_penalties(resp)
        log_flight_debug(resp)

        # ==========================
        # UPDATE STATE FIRST
        # ==========================
        state.ingest_response(resp)

        # ==========================
        # APPLY LANDINGS (BEFORE PURCHASE)
        # ==========================
        debug_print("--- LANDINGS ---")
        for ev in resp.flight_updates:
            if ev.event_type.value == "LANDED":
                loaded = strategy.last_loads.get(ev.flight_id)

                # Dacă n-am înregistrat încărcarea, considerăm 0 kits folosite
                if loaded is None:
                    loaded = PerClassAmount(0, 0, 0, 0)

                debug_print(
                    f"LANDED flight={ev.flight_number} "
                    f"({ev.flight_id}) used={loaded} "
                    f"→ {ev.destination_airport}"
                )

                sm.apply_landing(
                    airport=ev.destination_airport,
                    used_kits=loaded,
                    day=resp.day,
                    hour=resp.hour,
                )

                # Curățăm bufferul de load-uri
                strategy.last_loads.pop(ev.flight_id, None)

        # ==========================
        # APPLY PURCHASES (AFTER LANDING)
        # ==========================
        buy = req.kit_purchasing_orders
        if (buy.first or buy.business or
                buy.premium_economy or buy.economy):

            debug_print(
                f"PURCHASE fc={buy.first} bc={buy.business} "
                f"pe={buy.premium_economy} ec={buy.economy}"
            )

            sm.apply_purchase(
                buy.first,
                buy.business,
                buy.premium_economy,
                buy.economy,
            )

        # ==========================
        # COST TRACKING
        # ==========================
        total_cost = resp.total_cost
        hourly_cost = total_cost - prev_total_cost
        prev_total_cost = total_cost
        daily_costs.append(hourly_cost)

        debug_print(f"[ROUND] {resp.day}:{resp.hour} cost={total_cost}")

        # ==========================
        # STOCK SNAPSHOT
        # ==========================
        stock_snap = ", ".join(
            f"{ap}=FC:{st.fc} BC:{st.bc} PE:{st.pe} EC:{st.ec}"
            for ap, st in sm.stock.items()
        )
        debug_print(f"[STOCKS] {resp.day}:{resp.hour} {stock_snap}")

        # ==========================
        # END OF DAY SUMMARY
        # ==========================
        if resp.hour == 23:
            day_total = sum(daily_costs)
            avg_cost = day_total / len(daily_costs)
            end_day = resp.total_cost

            debug_print(
                f"[DAY] {resp.day} dailyTotal={day_total:.2f} "
                f"avgCost={avg_cost:.2f} endOfDayCost={end_day:.2f}"
            )

            daily_costs = []

        # ==========================
        # STOP CONDITION (END OF GAME)
        # ==========================
        if resp.day == 29 and resp.hour == 23:
            break

        # NEXT HOUR
        hour += 1
        if hour == 24:
            hour = 0
            day += 1

    debug_print("\n=== SIMULATION END ===")
    debug_print("SESSION CLOSED BY BACKEND")


if __name__ == "__main__":
    main()
