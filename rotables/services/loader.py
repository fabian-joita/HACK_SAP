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
