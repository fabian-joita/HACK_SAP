from dataclasses import dataclass

@dataclass
class FlightPlanEntry:
    id: str
    flight_number: str
    origin_airport_id: str
    destination_airport_id: str
    sched_aircraft_type_id: str
    scheduled_depart_day: int
    scheduled_depart_hour: int
    scheduled_arrival_day: int
    scheduled_arrival_hour: int
    distance: float
