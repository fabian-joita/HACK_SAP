class SessionController:
    def __init__(self, api_client, state, strategy, simulator):
        self.api = api_client
        self.state = state
        self.strategy = strategy
        self.sim = simulator

    def handle_scheduled(self, event):
        # transformă event în FlightInstance sau folosește direct fp
        pass

    def handle_checked_in(self, event):
        pass

    def handle_landed(self, event):
        # programezi movement pentru procesare kituri
        pass

    def next_round(self, day, hour):
        # 1. procesezi evenimente primite
        # 2. aplici movement-uri
        # 3. calculezi load pentru zboruri
        # 4. trimiți la API
        pass
