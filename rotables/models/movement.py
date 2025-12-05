from dataclasses import dataclass

@dataclass
class Movement:
    day: int
    hour: int
    airport_id: str
    cabin_class: str
    delta: int  # + kits or - kits
