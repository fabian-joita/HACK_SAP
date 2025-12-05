# rotables/dto/dto.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from uuid import UUID
from enum import Enum

# ---------------------------------------------------------
# ENUMS
# ---------------------------------------------------------

class FlightEventType(Enum):
    SCHEDULED = "SCHEDULED"
    CHECKED_IN = "CHECKED_IN"
    LANDED = "LANDED"


# ---------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------

@dataclass
class PerClassAmount:
    first: int = 0
    business: int = 0
    premium_economy: int = 0
    economy: int = 0

    def to_json(self):
        return {
            "first": self.first,
            "business": self.business,
            "premiumEconomy": self.premium_economy,
            "economy": self.economy
        }

    @staticmethod
    def from_json(js):
        if js is None:
            return PerClassAmount()
        return PerClassAmount(
            first=js.get("first", 0),
            business=js.get("business", 0),
            premium_economy=js.get("premiumEconomy", 0),
            economy=js.get("economy", 0),
        )


@dataclass
class FlightLoad:
    flight_id: UUID
    loaded_kits: PerClassAmount

    def to_json(self):
        return {
            "flightId": str(self.flight_id),
            "loadedKits": self.loaded_kits.to_json()
        }


@dataclass
class HourRequest:
    day: int
    hour: int
    flight_loads: List[FlightLoad] = field(default_factory=list)
    kit_purchasing_orders: PerClassAmount = field(default_factory=PerClassAmount)

    def to_json(self):
        return {
            "day": self.day,
            "hour": self.hour,
            "flightLoads": [f.to_json() for f in self.flight_loads],
            "kitPurchasingOrders": self.kit_purchasing_orders.to_json()
        }


# ---------------------------------------------------------
# RESPONSE MODELS
# ---------------------------------------------------------

@dataclass
class ReferenceHour:
    day: int
    hour: int

    @staticmethod
    def from_json(js):
        return ReferenceHour(
            day=js["day"],
            hour=js["hour"]
        )


@dataclass
class FlightEvent:
    event_type: FlightEventType
    flight_number: str
    flight_id: UUID
    origin_airport: str
    destination_airport: str
    departure: ReferenceHour
    arrival: ReferenceHour
    passengers: PerClassAmount
    aircraft_type: str

    @staticmethod
    def from_json(js):
        return FlightEvent(
            event_type=FlightEventType(js["eventType"]),
            flight_number=js["flightNumber"],
            flight_id=UUID(js["flightId"]),
            origin_airport=js["originAirport"],
            destination_airport=js["destinationAirport"],
            departure=ReferenceHour.from_json(js["departure"]),
            arrival=ReferenceHour.from_json(js["arrival"]),
            passengers=PerClassAmount.from_json(js["passengers"]),
            aircraft_type=js["aircraftType"]
        )


@dataclass
class Penalty:
    code: str
    flight_id: Optional[UUID]
    flight_number: Optional[str]
    issued_day: int
    issued_hour: int
    amount: float
    reason: str

    @staticmethod
    def from_json(js):
        return Penalty(
            code=js["code"],
            flight_id=UUID(js["flightId"]) if js.get("flightId") else None,
            flight_number=js.get("flightNumber"),
            issued_day=js["issuedDay"],
            issued_hour=js["issuedHour"],
            amount=js["penalty"],
            reason=js["reason"]
        )


@dataclass
class HourResponse:
    day: int
    hour: int
    flight_updates: List[FlightEvent]
    penalties: List[Penalty]
    total_cost: float

    @staticmethod
    def from_json(js):
        return HourResponse(
            day=js["day"],
            hour=js["hour"],
            flight_updates=[
                FlightEvent.from_json(f) for f in (js.get("flightUpdates") or [])
            ],
            penalties=[
                Penalty.from_json(p) for p in (js.get("penalties") or [])
            ],
            total_cost=js["totalCost"]
        )
