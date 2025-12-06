# rotables/controllers/session_controller.py

from rotables.dto.dto import HourRequest, PerClassAmount, FlightEventType

class SessionController:
    def __init__(self, api_client, game_state, state_manager, strategy):
        self.api = api_client
        self.gs = game_state
        self.sm = state_manager
        self.strategy = strategy

        self.current_day = 0
        self.current_hour = 0

    def next_round(self):

        # always use backend-synced time
        req = HourRequest(
            day=self.current_day,
            hour=self.current_hour,
            flight_loads=[],
            kit_purchasing_orders=PerClassAmount()
        )

        # === 1. send request ===
        response = self.api.play_round(req)

        # === 2. state update ===
        self.gs.ingest_response(response)

        for ev in response.flight_updates:
            if ev.event_type == FlightEventType.SCHEDULED:
                self.sm.on_scheduled(ev)
            elif ev.event_type == FlightEventType.CHECKED_IN:
                self.sm.on_checked_in(ev)
            elif ev.event_type == FlightEventType.LANDED:
                self.sm.on_landed(ev)

        self.sm.apply_movements(self.current_day, self.current_hour)

        # === 3. strategy ===
        strategy_req = self.strategy.build_hour_request(
            self.current_day,
            self.current_hour,
            self.gs,
            self.sm
        )

        # consume inventory after decision
        for fl in strategy_req.flight_loads:
            ev = self.gs.flights.get(fl.flight_id)
            if ev:
                self.sm.consume_inventory(ev.origin_airport, fl.loaded_kits)

        # === 4. send loads decision ===
        final = self.api.play_round(strategy_req)

        # === 5. update backend time ===
        self.current_day = final.day
        self.current_hour = final.hour

        return final
