from dataclasses import dataclass

@dataclass
class Airport:
    id: str
    code: str
    name: str

    # processing time per class
    first_processing_time: int
    business_processing_time: int
    premium_economy_processing_time: int
    economy_processing_time: int

    # processing cost per class
    first_processing_cost: float
    business_processing_cost: float
    premium_economy_processing_cost: float
    economy_processing_cost: float

    # loading cost per class
    first_loading_cost: float
    business_loading_cost: float
    premium_economy_loading_cost: float
    economy_loading_cost: float

    # stocks
    initial_fc_stock: int
    initial_bc_stock: int
    initial_pe_stock: int
    initial_ec_stock: int

    # capacities
    capacity_fc: int
    capacity_bc: int
    capacity_pe: int
    capacity_ec: int
