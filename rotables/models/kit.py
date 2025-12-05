from dataclasses import dataclass

@dataclass
class KitType:
    class_name: str
    cost: float
    weight: float
    lead_time: int
