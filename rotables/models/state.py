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
    State curat, compatibil StrategyAdvanced & StateManager.

    - active_flights: zboruri relevante "acum" (în special CHECKED_IN – de încărcat)
    - future_flights: zboruri programate / viitoare (folosite pentru forecast)
    """

    aircraft_caps: Dict[str, Dict] = field(default_factory=dict)

    # zboruri active (în special CHECKED_IN, adică de încărcat)
    active_flights: Dict[UUID, FlightEvent] = field(default_factory=dict)

    # zboruri în viitor (programate / în pipeline) – pentru forecast
    future_flights: Dict[UUID, FlightEvent] = field(default_factory=dict)

    # zboruri ce trebuie încărcate ACUM (CHECKED_IN)
    to_load: List[FlightEvent] = field(default_factory=list)

    # zboruri aterizate ACUM
    landed_now: List[FlightEvent] = field(default_factory=list)

    # log cost / timeline
    timeline_log: List[Dict] = field(default_factory=list)

    # ------------------------------------------------------------------
    def ingest_response(self, resp: HourResponse) -> None:
        """
        Actualizează state-ul cu update-urile primite pentru ora curentă.
        """

        # resetăm "evenimentele de acum"
        self.to_load = []
        self.landed_now = []

        for ev in resp.flight_updates:

            # ----------------------------------------------------------
            # debug special pe un anumit zbor (cum aveai deja)
            # ----------------------------------------------------------
            if ev.flight_number == "AB1105":
                log_debug(
                    resp.day,
                    resp.hour,
                    source="STATE",
                    event_type=ev.event_type.value,
                    ev=ev,
                    note="Event ingested",
                )

            # ----------------------------------------------------------
            # FUTURE_FLIGHTS – păstrăm zborurile programate / viitoare
            # ----------------------------------------------------------
            if ev.event_type in (FlightEventType.SCHEDULED, FlightEventType.CHECKED_IN):
                # zbor programat sau deja check-in -> există în viitor
                self.future_flights[ev.flight_id] = ev
            elif ev.event_type == FlightEventType.LANDED:
                # zbor aterizat -> dispare din viitor
                self.future_flights.pop(ev.flight_id, None)

            # ----------------------------------------------------------
            # ACTIVE_FLIGHTS – zboruri relevante "acum"
            # ----------------------------------------------------------
            if ev.event_type == FlightEventType.CHECKED_IN:
                # zbor care trebuie încărcat acum
                self.active_flights[ev.flight_id] = ev
            elif ev.event_type == FlightEventType.LANDED:
                # zbor aterizat -> nu mai e activ
                self.active_flights.pop(ev.flight_id, None)

            # ----------------------------------------------------------
            # Clasificare evenimente pentru strategie
            # ----------------------------------------------------------
            if ev.event_type == FlightEventType.CHECKED_IN:
                # trebuie încărcat ACUM
                self.to_load.append(ev)

            elif ev.event_type == FlightEventType.LANDED:
                # tocmai a aterizat
                self.landed_now.append(ev)

            # NOTĂ: pentru SCHEDULED nu facem nimic special aici, doar îl
            # ținem în future_flights.

        # log de cost / timeline
        self.timeline_log.append(
            {
                "day": resp.day,
                "hour": resp.hour,
                "total_cost": resp.total_cost,
            }
        )

    # ------------------------------------------------------------------
    def pop_flights_to_load(self) -> List[FlightEvent]:
        """
        Returnează lista zborurilor care trebuie încărcate în ora curentă.
        (copie, ca să nu stricăm lista internă)
        """
        return list(self.to_load)

    # ------------------------------------------------------------------
    def get_landed_flights(self) -> List[FlightEvent]:
        """
        Returnează lista zborurilor aterizate în ora curentă.
        """
        return list(self.landed_now)