# rotables/models/state.py

from dataclasses import dataclass, field
from typing import Dict, List
from uuid import UUID

# Import DTOs and logger as before
from rotables.dto.dto import HourResponse, FlightEvent, FlightEventType
from rotables.services.debug_logger import log_debug

from rotables.dto.dto import (
    HourResponse,
    FlightEvent,
    FlightEventType,
)

from rotables.services.debug_logger import log_debug


@dataclass
class GameState:
    """
    Starea completă:
    - memorează ultimele evenimente (SCHEDULED / CHECKED_IN / LANDED)
    - oferă zborurile CHECKED_IN care trebuie încărcate ACUM
    """

    # --- NEW STATIC DATA FIELDS ---
    # These must be loaded once and stored here for the Planner and Strategy
    flight_plan: Dict[str, 'FlightPlanEntry'] = field(default_factory=dict)
    airports: Dict[str, 'Airport'] = field(default_factory=dict)
    aircraft_types: Dict[str, 'AircraftType'] = field(default_factory=dict)
    # ------------------------------

    # --- NEW FIELD REQUIRED FOR THE FIX ---
    # This stores the specific flight instances from flights.csv (keyed by UUID)
    flight_schedule: Dict[str, 'FlightInstance'] = field(default_factory=dict) 
    # --------------------------------------

    aircraft_caps: Dict[str, Dict] = field(default_factory=dict)

    flights: Dict[UUID, FlightEvent] = field(default_factory=dict)

    timeline_log: List[Dict] = field(default_factory=list)


    # ---------------------------------------------------------------------
    # INGEST RESPONSE
    # ---------------------------------------------------------------------
    def ingest_response(self, resp: HourResponse):
        """Introducem evenimentele noi în state și logăm AB1105."""

        for ev in resp.flight_updates:
            self.flights[ev.flight_id] = ev

            if ev.flight_number == "AB1105":
                log_debug(resp.day, resp.hour,
                          source="STATE",
                          event_type=ev.event_type.value,
                          ev=ev,
                          note="Backend update ingested into state")

        # log cost
        self.timeline_log.append({
            "day": resp.day,
            "hour": resp.hour,
            "total_cost": resp.total_cost
        })

    # ---------------------------------------------------------------------
    # RETURNAREA ZBORURILOR CARE TREBUIE ÎNCĂRCATE ACUM
    # ---------------------------------------------------------------------
    def pop_flights_to_load(self) -> List[FlightEvent]:
        """
        Returnează zborurile CHECKED_IN.
        Nu șterge din state.
        Marchez un flag intern ca să nu le încărcăm de două ori.
        """

        result = []

        for ev in self.flights.values():

            if ev.event_type == FlightEventType.CHECKED_IN:

                # DEBUG 1 – detectăm CHECKED_IN
                if ev.flight_number == "AB1105":
                    log_debug(-1, -1,
                              source="STATE",
                              event_type="CHECKED_IN_SEEN",
                              ev=ev,
                              note="Detected CHECKED_IN in stored flights")

                # dacă nu a fost încărcat deja
                if not hasattr(ev, "_already_loaded"):
                    setattr(ev, "_already_loaded", True)
                    result.append(ev)

                    # DEBUG 2 – marcat pentru load
                    if ev.flight_number == "AB1105":
                        log_debug(-1, -1,
                                  source="STATE",
                                  event_type="READY_TO_LOAD",
                                  ev=ev,
                                  note="Flight marked for loading this round")

        return result
