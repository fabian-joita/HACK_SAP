import csv
from pathlib import Path

class Loader:
    def __init__(self, data_path="rotables/data"):
        self.data_path = Path(data_path)

    def load_aircraft_types(self):
        path = self.data_path / "aircraft_types.csv"
        aircraft = {}
        with path.open() as f:
            r = csv.DictReader(f, delimiter=";")
            for row in r:
                aircraft[row["type_code"]] = {
                    "fc": int(row["first_class_kits_capacity"]),
                    "bc": int(row["business_kits_capacity"]),
                    "pe": int(row["premium_economy_kits_capacity"]),
                    "ec": int(row["economy_kits_capacity"]),
                }
        return aircraft

    def load_airports_with_stocks(self):
        """Load airport data including initial stocks and other properties."""
        path = self.data_path / "airports_with_stocks.csv"
        airports = {}
        with path.open() as f:
            r = csv.DictReader(f, delimiter=";")
            for row in r:
                airports[row["id"]] = {
                    "code": row.get("code"),
                    "initial_fc_stock": int(row.get("initial_fc_stock", 0)),
                    "initial_bc_stock": int(row.get("initial_bc_stock", 0)),
                    "initial_pe_stock": int(row.get("initial_pe_stock", 0)),
                    "initial_ec_stock": int(row.get("initial_ec_stock", 0)),
                    "capacity_fc": int(row.get("capacity_fc", 9999)),
                    "capacity_bc": int(row.get("capacity_bc", 9999)),
                    "capacity_pe": int(row.get("capacity_pe", 9999)),
                    "capacity_ec": int(row.get("capacity_ec", 9999)),
                    "processing_time_fc": int(row.get("processing_time_fc", 2)),
                    "processing_time_bc": int(row.get("processing_time_bc", 2)),
                    "processing_time_pe": int(row.get("processing_time_pe", 2)),
                    "processing_time_ec": int(row.get("processing_time_ec", 2)),
                    "loading_cost_fc": float(row.get("loading_cost_fc", 1.0)),
                    "loading_cost_bc": float(row.get("loading_cost_bc", 1.0)),
                    "loading_cost_pe": float(row.get("loading_cost_pe", 1.0)),
                    "loading_cost_ec": float(row.get("loading_cost_ec", 1.0)),
                    "processing_cost_fc": float(row.get("processing_cost_fc", 0.5)),
                    "processing_cost_bc": float(row.get("processing_cost_bc", 0.5)),
                    "processing_cost_pe": float(row.get("processing_cost_pe", 0.5)),
                    "processing_cost_ec": float(row.get("processing_cost_ec", 0.5)),
                    "is_hub": row.get("code", "").startswith("HUB"),
                }
        return airports

