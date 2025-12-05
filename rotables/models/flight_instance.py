from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

@dataclass
class FlightInstance:
    flight_id: str
    flight_number: str
    origin: str
    destination: str

    aircraft_type: Optional[str] = None
    passengers_planned: Dict[str, int] = field(default_factory=dict)
    passengers_actual: Dict[str, int] = field(default_factory=dict)

    dep_planned: Optional[Tuple[int, int]] = None
    dep_actual: Optional[Tuple[int, int]] = None

    arr_planned: Optional[Tuple[int, int]] = None
    arr_actual: Optional[Tuple[int, int]] = None

    loaded_kits: Dict[str, int] = field(default_factory=dict)
