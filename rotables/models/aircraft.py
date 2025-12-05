from dataclasses import dataclass

@dataclass
class AircraftType:
    id: str
    type_code: str
    first_seats: int
    business_seats: int
    premium_economy_seats: int
    economy_seats: int
    cost_per_kg_per_km: float

    first_kits_capacity: int
    business_kits_capacity: int
    premium_economy_kits_capacity: int
    economy_kits_capacity: int
