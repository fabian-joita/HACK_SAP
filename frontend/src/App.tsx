import React, { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import StockTable from "./components/StockTable";

type DailyTotal = { day: number; dailyTotal: number };
type RotablesUsage = {
  day: number;
  FC: number;
  BC: number;
  PE: number;
  EC: number;
};

interface Stock {
  name: string;
  FC: number;
  BC: number;
  PE: number;
  EC: number;
}

const App: React.FC = () => {
  const [dailyTotals, setDailyTotals] = useState<DailyTotal[]>([]);
  const [rotablesUsage, setRotablesUsage] = useState<RotablesUsage[]>([]);
  const [finalStocks, setFinalStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(true);

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/run-main");
      const data = await res.json();
      if (data.success) {
        setDailyTotals(data.dailyTotals || []);
        setRotablesUsage(data.rotablesUsage || []);
        setFinalStocks(data.finalStocks || []);
      }
    } catch (err) {
      console.error("Backend connection failed");
    }
    setLoading(false);
  };

  const totalCost = dailyTotals.reduce((s, d) => s + d.dailyTotal, 0);
  const highest = dailyTotals.length
    ? Math.max(...dailyTotals.map((d) => d.dailyTotal))
    : 0;
  const lowest = dailyTotals.length
    ? Math.min(...dailyTotals.map((d) => d.dailyTotal))
    : 0;

  const totalFC = rotablesUsage.reduce((s, r) => s + r.FC, 0);
  const totalBC = rotablesUsage.reduce((s, r) => s + r.BC, 0);
  const totalPE = rotablesUsage.reduce((s, r) => s + r.PE, 0);
  const totalEC = rotablesUsage.reduce((s, r) => s + r.EC, 0);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: darkMode ? "#111418" : "#f0f0f0",
        color: darkMode ? "white" : "black",
        paddingTop: "100px",
        paddingLeft: "20px",
        paddingRight: "20px",
        transition: "0.3s",
      }}
    >
      {/* NAVBAR */}
      <div className={`navbar ${darkMode ? "navbar-dark" : "navbar-light"}`}>
        <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>
          ✈️ Rotables Simulator
        </div>

        <button onClick={() => setDarkMode(!darkMode)} className="toggle-btn">
          {darkMode ? "Light Mode" : "Dark Mode"}
        </button>
      </div>

      {/* CONTENT WRAPPER */}
      <div style={{ maxWidth: "1300px", margin: "0 auto" }}>
        <h1 className="title">Simulation Dashboard</h1>
        <div className="subtitle">Airline Rotables Logistics Analytics</div>

        {/* RUN BUTTON */}
        <button onClick={runSimulation} className="run-btn">
          {loading ? "✈️ Running Simulation..." : "Run Simulation"}
        </button>

        {/* PROGRESS BAR */}
        {loading && (
          <div className="progress-container fade-in">
            <div className="progress-track">
              <div className="progress-bar"></div>
            </div>
          </div>
        )}

        {/* TOTAL COST */}
        {dailyTotals.length > 0 && (
          <div className="total-cost-text">
            Total Cost: <span>{totalCost.toFixed(2)}</span>
          </div>
        )}

        {/* SUMMARY CARD */}
        {dailyTotals.length > 0 && (
          <div className="summary-card fade-in">
            <div>
              <h3>Simulation Summary</h3>
              <div>Total Days: {dailyTotals.length}</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div>Highest Day: {highest.toFixed(2)}</div>
              <div>Lowest Day: {lowest.toFixed(2)}</div>
            </div>
          </div>
        )}

        {/* DAILY COST CHART */}
        {dailyTotals.length > 0 && (
          <div className="chart-card fade-in">
            <h2>Daily Costs</h2>

            <div style={{ width: "100%", height: 350 }}>
              <ResponsiveContainer>
                <LineChart data={dailyTotals}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke={darkMode ? "#555" : "#ccc"}
                  />
                  <XAxis dataKey="day" stroke={darkMode ? "white" : "black"} />
                  <YAxis stroke={darkMode ? "white" : "black"} />
                  <Tooltip
                    wrapperStyle={{ background: darkMode ? "#222" : "white" }}
                  />
                  <Legend
                    wrapperStyle={{ color: darkMode ? "white" : "black" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="dailyTotal"
                    stroke="#ff6b6b"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* ROTABLES USAGE CHART */}
        {rotablesUsage.length > 0 && (
          <div className="chart-card fade-in">
            <h2>Daily Rotables Usage</h2>

            <div style={{ width: "100%", height: 350 }}>
              <ResponsiveContainer>
                <LineChart data={rotablesUsage}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke={darkMode ? "#555" : "#ccc"}
                  />
                  <XAxis dataKey="day" stroke={darkMode ? "white" : "black"} />
                  <YAxis stroke={darkMode ? "white" : "black"} />
                  <Tooltip
                    wrapperStyle={{ background: darkMode ? "#222" : "white" }}
                  />
                  <Legend
                    wrapperStyle={{ color: darkMode ? "white" : "black" }}
                  />

                  <Line
                    type="monotone"
                    dataKey="FC"
                    stroke="#a78bfa"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="BC"
                    stroke="#4ade80"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="PE"
                    stroke="#facc15"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="EC"
                    stroke="#fb923c"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* KPI CARDS */}
        {rotablesUsage.length > 0 && (
          <div className="kpi-grid fade-in">
            {[
              {
                label: "Total FC Used",
                value: totalFC,
                color: "#a78bfa",
                icon: "🟪",
              },
              {
                label: "Total BC Used",
                value: totalBC,
                color: "#4ade80",
                icon: "🟩",
              },
              {
                label: "Total PE Used",
                value: totalPE,
                color: "#facc15",
                icon: "🟨",
              },
              {
                label: "Total EC Used",
                value: totalEC,
                color: "#fb923c",
                icon: "🟧",
              },
            ].map((k, index) => (
              <div
                key={index}
                className="kpi-card"
                style={{ background: darkMode ? "#1c1f25" : "white" }}
              >
                <div className="kpi-icon">{k.icon}</div>
                <div className="kpi-label">{k.label}</div>
                <div className="kpi-value" style={{ color: k.color }}>
                  {k.value.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* STOCK TABLE */}
        {finalStocks.length > 0 && (
          <div className="chart-card fade-in">
            <h2>Final Airport Stocks</h2>
            <StockTable stocks={finalStocks} dark={darkMode} />
          </div>
        )}

        <div className="footer-text">
          Airline Rotables Simulator © {new Date().getFullYear()}
        </div>
      </div>
    </div>
  );
};

export default App;
