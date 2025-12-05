# rotables/services/debug_logger.py

import csv
import os

EVENT_LOG   = "backend_events.csv"
PENALTY_LOG = "backend_penalties.csv"
REQUEST_LOG = "backend_requests.csv"
DEBUG_LOG   = "flight_debug.csv"

# -----------------------------------------------------------
# DEBUG LOGGER -> scrie în CSV, NU în terminal
# -----------------------------------------------------------
DEBUG_OUTPUT = "debug_output.csv"

# initialize CSV dacă nu există
if not os.path.exists(DEBUG_OUTPUT):
    with open(DEBUG_OUTPUT, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "day", "hour", "source", "event_type", "flight_number",
            "flight_id", "fc", "bc", "pe", "ec", "note"
        ])


def log_debug(*args, **kwargs):
    """
    Log de debug care SCRIE ÎN CSV în loc să printeze.
    Așteaptă argumente de forma:
       log_debug(day, hour, source, event_type, ev, fc=..., bc=..., ...)
    """
    # extragem datele obligatorii
    if len(args) < 4:
        return  # format invalid -> ignorăm

    day  = args[0]
    hour = args[1]
    source = args[2]
    event_type = args[3]

    # dacă avem un FlightEvent ca al 5-lea argument
    flight_number = None
    flight_id = None
    if len(args) >= 5:
        ev = args[4]
        try:
            flight_number = ev.flight_number
            flight_id = str(ev.flight_id)
        except:
            pass

    # extragem kits (fc,bc,pe,ec,note)
    fc  = kwargs.get("fc")
    bc  = kwargs.get("bc")
    pe  = kwargs.get("pe")
    ec  = kwargs.get("ec")
    note = kwargs.get("note", "")

    # scriem în CSV
    with open(DEBUG_OUTPUT, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            day, hour, source, event_type, flight_number,
            flight_id, fc, bc, pe, ec, note
        ])

# -----------------------------------------------------------
# INTERNAL: write a row to CSV
# -----------------------------------------------------------
def write_row(filename, row):
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)


# -----------------------------------------------------------
# LOG REQUESTS (what we send to /play/round)
# -----------------------------------------------------------
def log_request(day, hour, req, state):
    """
    req.flight_loads: list[FlightLoad]
    FlightLoad has: flight_id, loaded_kits (PerClassAmount)
    Extra flight info is taken from state.flights[flight_id] if available.
    """
    flights_index = getattr(state, "flights", {}) if state is not None else {}

    for fl in req.flight_loads:
        ev = flights_index.get(fl.flight_id)

        if ev is not None:
            flight_number = ev.flight_number
            origin        = ev.origin_airport
            destination   = ev.destination_airport
            dep_day       = ev.departure.day
            dep_hour      = ev.departure.hour
            arr_day       = ev.arrival.day
            arr_hour      = ev.arrival.hour
        else:
            # Fallback if we somehow don't know the flight yet
            flight_number = None
            origin        = None
            destination   = None
            dep_day       = None
            dep_hour      = None
            arr_day       = None
            arr_hour      = None

        lk = fl.loaded_kits

        write_row(
            REQUEST_LOG,
            [
                day,
                hour,
                flight_number,
                str(fl.flight_id),
                origin,
                destination,
                dep_day,
                dep_hour,
                arr_day,
                arr_hour,
                lk.first,
                lk.business,
                lk.premium_economy,
                lk.economy,
            ],
        )


# -----------------------------------------------------------
# LOG EVENTS (SCHEDULED / CHECKED_IN / LANDED from backend)
# -----------------------------------------------------------
def log_events(resp):
    """
    resp: HourResponse
    resp.flight_updates: list[FlightEvent]
    """
    for ev in resp.flight_updates:
        pax = ev.passengers
        write_row(
            EVENT_LOG,
            [
                resp.day,
                resp.hour,
                ev.event_type.value,
                ev.flight_number,
                str(ev.flight_id),
                ev.origin_airport,
                ev.destination_airport,
                ev.departure.day,
                ev.departure.hour,
                ev.arrival.day,
                ev.arrival.hour,
                pax.first,
                pax.business,
                pax.premium_economy,
                pax.economy,
                resp.total_cost,
            ],
        )


# -----------------------------------------------------------
# LOG PENALTIES
# -----------------------------------------------------------
def log_penalties(resp):
    """
    resp.penalties: list[Penalty]
    Penalty has: code, amount, reason, flight_number, flight_id, ...
    """
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
# LOG DEBUG INFO PER FLIGHT (currently no backend debug_info)
# -----------------------------------------------------------
def log_flight_debug(resp):
    """
    The backend HourResponse does not expose extra debug info,
    so we keep this as a no-op for now to match the call in main.py.
    """
    return
