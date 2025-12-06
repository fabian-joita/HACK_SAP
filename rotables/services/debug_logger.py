import csv
import os

EVENT_LOG   = "backend_events.csv"
PENALTY_LOG = "backend_penalties.csv"
REQUEST_LOG = "backend_requests.csv"
DEBUG_LOG   = "flight_debug.csv"
DEBUG_OUTPUT = "debug_output.csv"

# -----------------------------------------------------------
# RESET FILES ON EVERY RUN (IMPORTANT)
# -----------------------------------------------------------

def _reset_csv(filename, header):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

# run reset EXACTLY ON IMPORT
_reset_csv(EVENT_LOG, [
    "day","hour","event_type","flight_number","flight_id",
    "origin","destination","dep_day","dep_hour",
    "arr_day","arr_hour","pax_fc","pax_bc","pax_pe","pax_ec","total_cost"
])

_reset_csv(PENALTY_LOG, [
    "day","hour","code","amount","reason",
    "flight_number","flight_id","total_cost"
])

_reset_csv(REQUEST_LOG, [
    "day","hour","flight_number","flight_id","origin","destination",
    "dep_day","dep_hour","arr_day","arr_hour",
    "load_fc","load_bc","load_pe","load_ec"
])

_reset_csv(DEBUG_LOG, [
    "day","hour","message"
])

_reset_csv(DEBUG_OUTPUT, [
    "day","hour","source","event_type","flight_number",
    "flight_id","fc","bc","pe","ec","note"
])

# -----------------------------------------------------------
# INTERNAL: append row to CSV
# -----------------------------------------------------------
def write_row(filename, row):
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

# -----------------------------------------------------------
# DEBUG (writes to debug_output.csv)
# -----------------------------------------------------------
def log_debug(*args, **kwargs):
    if len(args) < 4:
        return

    day  = args[0]
    hour = args[1]
    source = args[2]
    event_type = args[3]

    flight_number = None
    flight_id = None

    if len(args) >= 5:
        ev = args[4]
        try:
            flight_number = ev.flight_number
            flight_id = str(ev.flight_id)
        except:
            pass

    fc  = kwargs.get("fc")
    bc  = kwargs.get("bc")
    pe  = kwargs.get("pe")
    ec  = kwargs.get("ec")
    note = kwargs.get("note", "")

    write_row(
        DEBUG_OUTPUT,
        [day, hour, source, event_type, flight_number,
         flight_id, fc, bc, pe, ec, note]
    )

# -----------------------------------------------------------
# LOG REQUESTS
# -----------------------------------------------------------
def log_request(day, hour, req, state):
    flights_index = getattr(state, "flights", {}) if state is not None else {}

    for fl in req.flight_loads:
        ev = flights_index.get(fl.flight_id)

        if ev is not None:
            row = [
                day, hour,
                ev.flight_number,
                str(fl.flight_id),
                ev.origin_airport,
                ev.destination_airport,
                ev.departure.day,
                ev.departure.hour,
                ev.arrival.day,
                ev.arrival.hour,
                fl.loaded_kits.first,
                fl.loaded_kits.business,
                fl.loaded_kits.premium_economy,
                fl.loaded_kits.economy
            ]
        else:
            row = [
                day, hour,
                None,
                str(fl.flight_id),
                None, None,
                None, None,
                None, None,
                fl.loaded_kits.first,
                fl.loaded_kits.business,
                fl.loaded_kits.premium_economy,
                fl.loaded_kits.economy
            ]

        write_row(REQUEST_LOG, row)

# -----------------------------------------------------------
# LOG EVENTS
# -----------------------------------------------------------
def log_events(resp):
    for ev in resp.flight_updates:
        pax = ev.passengers
        write_row(
            EVENT_LOG,
            [
                resp.day, resp.hour,
                ev.event_type.value,
                ev.flight_number,
                str(ev.flight_id),
                ev.origin_airport,
                ev.destination_airport,
                ev.departure.day,
                ev.departure.hour,
                ev.arrival.day,
                ev.arrival.hour,
                pax.first, pax.business,
                pax.premium_economy, pax.economy,
                resp.total_cost
            ]
        )

# -----------------------------------------------------------
# LOG PENALTIES
# -----------------------------------------------------------
def log_penalties(resp):
    for p in resp.penalties:
        write_row(
            PENALTY_LOG,
            [
                resp.day,
                resp.hour,
                p.code,
                p.amount,
                p.reason,
                p.flight_number,
                str(p.flight_id) if p.flight_id else None,
                resp.total_cost,
            ],
        )

# -----------------------------------------------------------
# NO-OP (kept for compatibility)
# -----------------------------------------------------------
def log_flight_debug(resp):
    pass
