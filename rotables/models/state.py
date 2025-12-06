# rotables/models/state.py

from dataclasses import dataclass, field
from typing import Dict, List
from uuid import UUID

from rotables.dto.dto import (
    HourResponse,
    FlightEvent,
    FlightEventType,
)

from rotables.services.debug_logger import log_debug


@dataclass
class GameState:
    """
    State curat, compatibil Strategy B2 & StateManager.
    """

    aircraft_caps: Dict[str, Dict] = field(default_factory=dict)

    # doar zborurile active (CHECKED_IN, SCHEDULED)
    active_flights: Dict[UUID, FlightEvent] = field(default_factory=dict)

    # zboruri ce trebuie încărcate ACUM
    to_load: List[FlightEvent] = field(default_factory=list)

    # zboruri aterizate ACUM
    landed_now: List[FlightEvent] = field(default_factory=list)

    timeline_log: List[Dict] = field(default_factory=list)

    # ------------------------------------------------------------------
    def ingest_response(self, resp: HourResponse):

        self.to_load = []
        self.landed_now = []

        for ev in resp.flight_updates:

            # track raw
            self.active_flights[ev.flight_id] = ev

            # debug special
            if ev.flight_number == "AB1105":
                log_debug(resp.day, resp.hour,
                          source="STATE",
                          event_type=ev.event_type.value,
                          ev=ev,
                          note="Event ingested")

            # classify events
            if ev.event_type == FlightEventType.CHECKED_IN:
                self.to_load.append(ev)

            elif ev.event_type == FlightEventType.LANDED:
                self.landed_now.append(ev)

            elif ev.event_type == FlightEventType.SCHEDULED:
                # remove departed flight
                if ev.flight_id in self.active_flights:
                    del self.active_flights[ev.flight_id]

        # log cost
        self.timeline_log.append({
            "day": resp.day,
            "hour": resp.hour,
            "total_cost": resp.total_cost
        })

    # ------------------------------------------------------------------
    def pop_flights_to_load(self) -> List[FlightEvent]:
        return list(self.to_load)

    # ------------------------------------------------------------------
    def get_landed_flights(self) -> List[FlightEvent]:
        return list(self.landed_now)
