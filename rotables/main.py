# rotables/main.py

import csv
import os

from rotables.services.api_client import ApiClient
from rotables.services.loader import Loader
from rotables.services.strategy import Strategy
from rotables.models.state import GameState
from rotables.dto.dto import HourRequest, PerClassAmount
from rotables.services.debug_logger import (
    log_request,
    log_events,
    log_penalties,
    log_flight_debug
)

EVENT_LOG   = "backend_events.csv"
PENALTY_LOG = "backend_penalties.csv"
REQUEST_LOG = "backend_requests.csv"
DEBUG_LOG   = "flight_debug.csv"


def init_csv_files():
    files = {
        EVENT_LOG:   ["day","hour","event_type","flight_number","flight_id","origin","destination",
                      "dep_day","dep_hour","arr_day","arr_hour",
                      "pax_fc","pax_bc","pax_pe","pax_ec","total_cost"],

        PENALTY_LOG: ["day","hour","penalty_code","penalty_amount","reason",
                      "flight_number","flight_id","total_cost"],

        REQUEST_LOG: ["day","hour","flight_number","flight_id","origin","destination",
                      "dep_day","dep_hour","arr_day","arr_hour",
                      "load_fc","load_bc","load_pe","load_ec"],

        DEBUG_LOG:   ["day","hour","source","event_type",
                      "flight_number","flight_id",
                      "dep_day","dep_hour","arr_day","arr_hour",
                      "fc","bc","pe","ec","note"]
    }

    for filename, header in files.items():
        if not os.path.exists(filename):
            with open(filename, "w", newline="") as f:
                csv.writer(f).writerow(header)


def main():

    print("\n=== ROTABLES ENGINE START (LP OPTIMIZER) ===\n")

    init_csv_files()

    loader = Loader()
    aircraft_caps = loader.load_aircraft_types()
    state = GameState(aircraft_caps=aircraft_caps)
    api = ApiClient()
    strategy = Strategy()

    # ----------------------------------------------------------
    # DO NOT DELETE session.id ANYMORE!!!
    # ----------------------------------------------------------
    print("[INFO] Starting or resuming session...")
    api.start_session()

    # Try to detect current session time by making a test request
    day = 0
    hour = 0
    
    # Try with 0:0 first, if it fails, extract the expected time
    try:
        test_req = HourRequest(day=0, hour=0, flight_loads=[], 
                              kit_purchasing_orders=PerClassAmount(0, 0, 0, 0))
        resp = api.play_round(test_req)
        # If successful, we start from 0:0
        state.ingest_response(resp)
        log_events(resp)
        log_penalties(resp)
        log_flight_debug(resp)
        print(f"[ROUND] {resp.day}:{resp.hour} cost={resp.total_cost}")
        
        # Move to next hour
        hour = resp.hour + 1
        day = resp.day
        if hour == 24:
            hour = 0
            day += 1
    except RuntimeError as e:
        # Extract expected time from error message
        error_msg = str(e)
        if "expected time" in error_msg:
            import re
            match = re.search(r'expected time \((\d+):(\d+)\)', error_msg)
            if match:
                day = int(match.group(1))
                hour = int(match.group(2))
                print(f"[INFO] Resuming session from day={day}, hour={hour}")
            else:
                raise

    while True:
        req = strategy.build_hour_request(day, hour, state)
        log_request(day, hour, req, state)

        resp = api.play_round(req)

        state.ingest_response(resp)
        log_events(resp)
        log_penalties(resp)
        log_flight_debug(resp)

        print(f"[ROUND] {resp.day}:{resp.hour} cost={resp.total_cost}")

        if resp.day == 29 and resp.hour == 23:
            break

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
