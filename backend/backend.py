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
        # Run simulation
        result = subprocess.run(
            ["python3", "-m", "rotables.main"],
            cwd="../",
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout + "\n" + result.stderr

        # ============================================================
        # 1) PARSE ROUND LINES (format: [ROUND] 0:5 cost=2758909.68)
        # ============================================================
        round_matches = re.findall(
            r"\[ROUND\]\s*(\d+):(\d+)\s*cost=([-\d\.eE]+)",
            output
        )

        hourlyCosts = []
        prev_total = 0.0

        for d, h, total in round_matches:
            total_cost = float(total)
            hourly = total_cost - prev_total
            prev_total = total_cost

            hourlyCosts.append({
                "day": int(d),
                "hour": int(h),
                "hourlyCost": hourly,
                "totalCost": total_cost
            })

        # ============================================================
        # 2) PARSE DAY SUMMARY (full)
        #
        # [DAY] 0 dailyTotal=XXXXX avgCost=YYYY endOfDayCost=ZZZZ
        # ============================================================
        day_matches = re.findall(
            r"\[DAY\]\s*(\d+)\s+dailyTotal=([-\d\.eE]+)\s+avgCost=([-\d\.eE]+)\s+endOfDayCost=([-\d\.eE]+)",
            output
        )

        dailySummary = []
        for d, daily, avg, endday in day_matches:
            dailySummary.append({
                "day": int(d),
                "dailyTotal": float(daily),
                "avgCost": float(avg),
                "endOfDayCost": float(endday)
            })

        # ============================================================
        # 2B) PARSE ONLY dailyTotal (for daily graph)
        # ============================================================
        day_totals_raw = re.findall(
            r"\[DAY\]\s*(\d+)\s+dailyTotal=([-\d\.eE]+)",
            output
        )

        dailyTotals = [
            {"day": int(d), "dailyTotal": float(total)}
            for d, total in day_totals_raw
        ]

        # ============================================================
        # 3) PARSE STOCKS
        # ============================================================
        stock_matches = re.findall(r"\[STOCKS]\s+(\d+):(\d+)\s+(.*)", output)
        stocks_by_day = {}

        for d, h, stock_str in stock_matches:
            day, hour = int(d), int(h)

            entries = re.findall(
                r"(\w+)=FC:(\d+)\s+BC:(\d+)\s+PE:(\d+)\s+EC:(\d+)",
                stock_str
            )

            airport_stocks = {
                ap: {
                    "FC": int(fc),
                    "BC": int(bc),
                    "PE": int(pe),
                    "EC": int(ec)
                }
                for ap, fc, bc, pe, ec in entries
            }

            stocks_by_day.setdefault(day, []).append(airport_stocks)

        # ============================================================
        # 4) ROTABLES USAGE (per day)
        # ============================================================
        rotables_usage_per_day = {}

        for day, snapshots in stocks_by_day.items():
            daily = {"FC": 0, "BC": 0, "PE": 0, "EC": 0}

            for i in range(1, len(snapshots)):
                prev = snapshots[i - 1]
                curr = snapshots[i]

                airports = set(prev.keys()).union(curr.keys())

                for ap in airports:
                    for cls in daily:
                        diff = prev.get(ap, {}).get(cls, 0) - curr.get(ap, {}).get(cls, 0)
                        if diff > 0:
                            daily[cls] += diff

            rotables_usage_per_day[day] = daily

        rotablesUsage = [
            {"day": day, **usage}
            for day, usage in sorted(rotables_usage_per_day.items())
        ]

        # ============================================================
        # RETURN JSON FOR FRONTEND
        # ============================================================
        return {
            "success": True,
            "hourlyCosts": hourlyCosts,
            "dailySummary": dailySummary,
            "dailyTotals": dailyTotals,
            "rotablesUsage": rotablesUsage
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
