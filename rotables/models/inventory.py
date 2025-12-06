# rotables/models/inventory.py
from dataclasses import dataclass


@dataclass
class Inventory:
    fc: int = 0
    bc: int = 0
    pe: int = 0
    ec: int = 0


# Pentru claritate în StateManager
InventoryState = Inventory
