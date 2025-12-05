from collections import defaultdict
import math

class Planner:
    def __init__(self, state):
        self.state = state
        self.avg_daily_demand = defaultdict(lambda: {"fc":0,"bc":0,"pe":0,"ec":0})
        self._compute_avg_demand()

    def _compute_avg_demand(self):
        load_factor = 0.8
        horizon_days = 7

        for fp in self.state.flight_plan:
            ac = self.state.aircraft_types.get(fp.sched_aircraft_type_id)
            if not ac:
                continue

            a = self.avg_daily_demand[fp.origin_airport_id]
            a["fc"] += ac.first_seats * load_factor / horizon_days
            a["bc"] += ac.business_seats * load_factor / horizon_days
            a["pe"] += ac.premium_economy_seats * load_factor / horizon_days
            a["ec"] += ac.economy_seats * load_factor / horizon_days

    def target_stock(self, airport_id):
        ap = self.state.airports[airport_id]
        d = self.avg_daily_demand[airport_id]
        SAFETY_FACTOR = 1.2
        DAYS = 7

        def calc(key, cap):
            demand = d[key] * DAYS * SAFETY_FACTOR
            return min(math.ceil(demand), cap)

        return {
            "fc": calc("fc", ap.capacity_fc),
            "bc": calc("bc", ap.capacity_bc),
            "pe": calc("pe", ap.capacity_pe),
            "ec": calc("ec", ap.capacity_ec),
        }
