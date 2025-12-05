from typing import List
from rotables.dto.dto import HourRequest, FlightLoad, PerClassAmount, FlightEvent
from rotables.models.state import GameState
from rotables.services.debug_logger import log_debug


class Strategy:

    def build_hour_request(self, day: int, hour: int, state: GameState) -> HourRequest:

        flights_to_load = state.pop_flights_to_load()
        flight_loads: List[FlightLoad] = []

        for ev in flights_to_load:

            # debug AB1105
            if ev.flight_number == "AB1105":
                log_debug(day, hour, "STRATEGY", "CHECKED_IN", ev,
                          fc=ev.passengers.first,
                          bc=ev.passengers.business,
                          pe=ev.passengers.premium_economy,
                          ec=ev.passengers.economy,
                          note="Strategy sees flight to load")

            fl = self._decide_load(ev)
            flight_loads.append(fl)

        purchasing = PerClassAmount(0, 0, 0, 0)

        return HourRequest(
            day=day,
            hour=hour,
            flight_loads=flight_loads,
            kit_purchasing_orders=purchasing
        )

    def _decide_load(self, ev: FlightEvent) -> FlightLoad:
        return FlightLoad(
        flight_id=ev.flight_id,
        loaded_kits=PerClassAmount(0, 0, 0, 0)
    )