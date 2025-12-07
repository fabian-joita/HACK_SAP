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
    } catch {
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
    <div className={darkMode ? "dark" : "light"}>
      {/* NAVBAR */}
      <div className={`navbar ${darkMode ? "navbar-dark" : "navbar-light"}`}>
        <div className="nav-title">✈ Rotables Simulator</div>
        <button className="toggle-btn" onClick={() => setDarkMode(!darkMode)}>
          {darkMode ? "Light Mode" : "Dark Mode"}
        </button>
      </div>

      {/* MAIN CONTENT */}
      <div className="container" style={{ paddingTop: "120px" }}>
        {/* HEADER */}
        <header>
          <h1>Simulation Dashboard</h1>
          <div className="subtitle">Airline Rotables Logistics Analytics</div>
        </header>

        {/* RUN BUTTON */}
        <button className="run-btn" onClick={runSimulation}>
          {loading ? "✈ Running Simulation..." : "Run Simulation"}
        </button>

        {/* PROGRESS BAR */}
        {loading && (
          <div className="progress-container fade-in">
            <div className="progress-track">
              <div className="progress-bar"></div>
            </div>
          </div>
        )}

        {/* COST SUMMARY */}
        {dailyTotals.length > 0 && (
          <div className="results-section fade-in">
            <div className="results-header">
              <div>
                <h2>Total Cost</h2>
                <p className="final-score">{totalCost.toLocaleString()}</p>
              </div>

              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Highest Day</div>
                  <div className="metric-value">{highest.toLocaleString()}</div>
                </div>

                <div className="metric-card">
                  <div className="metric-label">Lowest Day</div>
                  <div className="metric-value">{lowest.toLocaleString()}</div>
                </div>

                <div className="metric-card">
                  <div className="metric-label">Total Days</div>
                  <div className="metric-value">{dailyTotals.length}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* DAILY COSTS */}
        {dailyTotals.length > 0 && (
          <div className="chart-container fade-in">
            <h3>Daily Costs</h3>
            <div style={{ width: "100%", height: 350 }}>
              <ResponsiveContainer>
                <LineChart data={dailyTotals}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="day" stroke="#e0e7ff" />
                  <YAxis stroke="#e0e7ff" />
                  <Tooltip />
                  <Legend />
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

        {/* ROTABLES USAGE */}
        {rotablesUsage.length > 0 && (
          <div className="chart-container fade-in">
            <h3>Daily Rotables Usage</h3>
            <div style={{ width: "100%", height: 350 }}>
              <ResponsiveContainer>
                <LineChart data={rotablesUsage}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="day" stroke="#e0e7ff" />
                  <YAxis stroke="#e0e7ff" />
                  <Tooltip />
                  <Legend />
                  <Line dataKey="FC" stroke="#a78bfa" strokeWidth={2} />
                  <Line dataKey="BC" stroke="#4ade80" strokeWidth={2} />
                  <Line dataKey="PE" stroke="#facc15" strokeWidth={2} />
                  <Line dataKey="EC" stroke="#fb923c" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* KPI CARDS */}
        {rotablesUsage.length > 0 && (
          <div className="scores-grid fade-in">
            <div className="score-card">
              <div className="score-label">Total FC Used</div>
              <div className="score-value">{totalFC.toLocaleString()}</div>
            </div>

            <div className="score-card">
              <div className="score-label">Total BC Used</div>
              <div className="score-value">{totalBC.toLocaleString()}</div>
            </div>

            <div className="score-card">
              <div className="score-label">Total PE Used</div>
              <div className="score-value">{totalPE.toLocaleString()}</div>
            </div>

            <div className="score-card">
              <div className="score-label">Total EC Used</div>
              <div className="score-value">{totalEC.toLocaleString()}</div>
            </div>
          </div>
        )}

        {/* STOCK TABLE */}
        {finalStocks.length > 0 && (
          <div className="chart-container fade-in">
            <h3>Final Airport Stocks</h3>
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
