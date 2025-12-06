# rotables/services/loader.py
import csv

from rotables.models.airport import Airport


class Loader:
    # ------------------------------------------------------------
    # 1) Load airports from airports_with_stocks.csv
    # ------------------------------------------------------------
    def load_airports(self):
        airports = []

        with open("rotables/data/airports_with_stocks.csv") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                ap = Airport(
                    id=row["id"],
                    code=row["code"],
                    name=row["name"],

                    first_processing_time=int(row["first_processing_time"]),
                    business_processing_time=int(row["business_processing_time"]),
                    premium_economy_processing_time=int(row["premium_economy_processing_time"]),
                    economy_processing_time=int(row["economy_processing_time"]),

                    first_processing_cost=float(row["first_processing_cost"]),
                    business_processing_cost=float(row["business_processing_cost"]),
                    premium_economy_processing_cost=float(row["premium_economy_processing_cost"]),
                    economy_processing_cost=float(row["economy_processing_cost"]),

                    first_loading_cost=float(row["first_loading_cost"]),
                    business_loading_cost=float(row["business_loading_cost"]),
                    premium_economy_loading_cost=float(row["premium_economy_loading_cost"]),
                    economy_loading_cost=float(row["economy_loading_cost"]),

                    initial_fc_stock=int(row["initial_fc_stock"]),
                    initial_bc_stock=int(row["initial_bc_stock"]),
                    initial_pe_stock=int(row["initial_pe_stock"]),
                    initial_ec_stock=int(row["initial_ec_stock"]),

                    capacity_fc=int(row["capacity_fc"]),
                    capacity_bc=int(row["capacity_bc"]),
                    capacity_pe=int(row["capacity_pe"]),
                    capacity_ec=int(row["capacity_ec"]),
                )
                airports.append(ap)

        return airports

    # ------------------------------------------------------------
    # 2) Load aircraft types → {type_code: {fc, bc, pe, ec}}
    # ------------------------------------------------------------
    def load_aircraft_types(self):
        aircraft = {}

        with open("rotables/data/aircraft_types.csv") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                aircraft[row["type_code"]] = {
                    "fc": int(row["first_class_kits_capacity"]),
                    "bc": int(row["business_kits_capacity"]),
                    "pe": int(row["premium_economy_kits_capacity"]),
                    "ec": int(row["economy_kits_capacity"]),
                }

        return aircraft
