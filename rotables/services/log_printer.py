# rotables/services/log_printer.py

from rotables.dto.dto import HourRequest, PerClassAmount
from rotables.models.inventory import InventoryState # Assuming InventoryState has fc, bc, pe, ec attributes
from rotables.services.inventory_simulator import InventorySimulator # Assuming this object holds the inventory dict

def print_round_log(day: int, hour: int, cost: float, req: HourRequest, simulator: InventorySimulator, landings: dict = None):
    """
    Prints a detailed log for the given hour, mimicking the provided format.
    
    Args:
        day: The game day for the DEBUG header (should be the next day/hour).
        hour: The game hour for the DEBUG header (should be the next day/hour).
        cost: The total current cost reported by the API (from the last response).
        req: The HourRequest object sent to the API (containing loads and purchases).
        simulator: The InventorySimulator instance (to get post-response stock).
        landings: A dict mapping flight_id to a PerClassAmount of used kits (from API response).
    """

    # --- 1. Cost and Header ---
    # The [ROUND] cost prints the result of the *last* round (H-1)
    if hour > 0 or day > 0: 
        # Calculate the previous hour for the [ROUND] tag, using the cost of the last response
        prev_hour = hour - 1
        prev_day = day
        if prev_hour == -1:
            prev_hour = 23
            prev_day -= 1
        
        # Only print the cost if we are past the very first 0:00 initialization
        if prev_day >= 0:
            print(f"\n[ROUND] {prev_day}:{prev_hour:02d} cost={cost:.14f}")
    
    print(f"\n==============================")
    print(f"⏰ DEBUG DAY {day} HOUR {hour:02d}")
    print(f"==============================")

    # --- 2. STOCK Levels ---
    # You must loop through ALL airports in simulator.inventory to match the user's log
    # We sort by airport_id to maintain a consistent log order.
    for airport_id, stock in sorted(simulator.inventory.items()):
        # Ensure the stock object has the required attributes (fc, bc, pe, ec)
        if hasattr(stock, 'fc'):
            print(f"STOCK[{airport_id}]  FC={stock.fc:<4} BC={stock.bc:<4} PE={stock.pe:<4} EC={stock.ec:<4}")
        # If the InventoryState DTO is not correctly structured, you might need to adjust here
        # Example: print(f"STOCK[{airport_id}]  FC={stock.first_class:<4}...")

    # --- 3. LOAD DECISIONS ---
    print("\n--- LOAD DECISIONS ---")
    for fl in req.flight_loads:
        kits: PerClassAmount = fl.loaded_kits
        print(f"LOAD  Flight={fl.flight_id}  FC={kits.first:<2}  BC={kits.business:<2}  PE={kits.premium_economy:<2}  EC={kits.economy:<2}")

    # --- 4. PURCHASING ---
    purchasing = req.kit_purchasing_orders
    print("\n--- PURCHASING ---")
    print(f"PerClassAmount(first={purchasing.first}, business={purchasing.business}, premium_economy={purchasing.premium_economy}, economy={purchasing.economy})")

    # --- 5. LANDINGS ---
    if landings:
        print("\n--- LANDINGS ---")
        # Landings is expected to be a dictionary structured like {flight_id: PerClassAmount(used_kits)}
        for flight_id, used_kits in landings.items():
             print(f"LANDING  Flight={flight_id}  Used=PerClassAmount(first={used_kits.first}, business={used_kits.business}, premium_economy={used_kits.premium_economy}, economy={used_kits.economy})")