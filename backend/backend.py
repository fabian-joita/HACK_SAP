# backend/backend.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/run-main")
def run_main():
    try:
        # Run the simulation
        result = subprocess.run(
            ["python3", "-m", "rotables.main"],
            cwd="../",
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout + "\n" + result.stderr

        # ---------------- Parse hourly costs ----------------
        round_matches = re.findall(r'\[ROUND\]\s+(\d+):(\d+)\s+cost=(\d+\.?\d*)', output)
        hourly_costs_flat = []
        last_hour_cost = {}
        for d, h, c in round_matches:
            day, hour, cost = int(d), int(h), float(c)
            hourly_costs_flat.append({"day": day, "hour": hour, "cost": cost})
            last_hour_cost[day] = cost  # store latest hour cost for each day

        # ---------------- Compute daily summary (cumulative correction) ----------------
        sorted_days = sorted(last_hour_cost.keys())
        daily_summary = []
        prev_total = 0.0
        cumulative_total = 0.0

        for day in sorted_days:
            curr_total = last_hour_cost[day]
            day_total = curr_total - prev_total  # today's cost only
            prev_total = curr_total
            cumulative_total += day_total
            avg_cost = cumulative_total / (day + 1)  # average cost per day including previous days
            daily_summary.append({
                "day": day,
                "endOfDayCost": day_total,
                "avgCost": avg_cost
            })

        # ---------------- Parse stock snapshots ----------------
        stock_matches = re.findall(r'\[STOCKS]\s+(\d+):(\d+)\s+(.*)', output)
        stocks_by_day = {}
        for d, h, stock_str in stock_matches:
            day, hour = int(d), int(h)
            airport_stocks = {}
            entries = re.findall(r'(\w+)=FC:(\d+)\s+BC:(\d+)\s+PE:(\d+)\s+EC:(\d+)', stock_str)
            for ap, fc, bc, pe, ec in entries:
                airport_stocks[ap] = {"FC": int(fc), "BC": int(bc), "PE": int(pe), "EC": int(ec)}
            stocks_by_day.setdefault(day, []).append(airport_stocks)

        # ---------------- Compute rotables usage per day ----------------
        rotables_usage_per_day = {}
        for day, hours in stocks_by_day.items():
            daily_usage = {"FC": 0, "BC": 0, "PE": 0, "EC": 0}
            for i in range(1, len(hours)):
                prev = hours[i-1]
                curr = hours[i]
                for ap in set(prev.keys()).union(curr.keys()):
                    for cls in ["FC", "BC", "PE", "EC"]:
                        prev_val = prev.get(ap, {}).get(cls, 0)
                        curr_val = curr.get(ap, {}).get(cls, 0)
                        used = max(prev_val - curr_val, 0)
                        daily_usage[cls] += used
            rotables_usage_per_day[day] = daily_usage

        # ---------------- Convert rotables usage dict to array ----------------
        rotables_usage_array = [
            {"day": day, **usage} for day, usage in sorted(rotables_usage_per_day.items())
        ]

        return {
            "success": True,
            "hourlyCosts": hourly_costs_flat,
            "dailySummary": daily_summary,
            "rotablesUsage": rotables_usage_array
        }

    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}
