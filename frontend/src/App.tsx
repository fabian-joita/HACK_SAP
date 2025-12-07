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
      <nav className="navbar">
        <div className="nav-title">✈ Rotables Simulator</div>
        <button className="toggle-btn" onClick={() => setDarkMode(!darkMode)}>
          {darkMode ? "Light Mode" : "Dark Mode"}
        </button>
      </nav>

      <main className="main-container">
        {/* HEADER */}
        <section className="hero-card">
          <h1 className="hero-title">Simulation Dashboard</h1>
          <p className="hero-subtitle">Airline Rotables Logistics Analytics</p>

          <button className="run-btn" onClick={runSimulation}>
            {loading ? "✈ Running Simulation..." : "Run Simulation"}
          </button>

          {loading && (
            <div className="progress-container">
              <div className="progress-track">
                <div className="progress-bar" />
              </div>
            </div>
          )}
        </section>

        {/* SUMMARY */}
        {dailyTotals.length > 0 && (
          <section className="card summary-card">
            <h2>Simulation Summary</h2>
            <div className="summary-grid">
              <div className="summary-item">
                <span>Total Cost </span>
                <strong>{totalCost.toLocaleString()}</strong>
              </div>
              <div className="summary-item">
                <span>Highest Day </span>
                <strong>{highest.toLocaleString()}</strong>
              </div>
              <div className="summary-item">
                <span>Lowest Day </span>
                <strong>{lowest.toLocaleString()}</strong>
              </div>
              <div className="summary-item">
                <span>Total Days </span>
                <strong>{dailyTotals.length}</strong>
              </div>
            </div>
          </section>
        )}

        {/* DAILY COST CHART */}
        {dailyTotals.length > 0 && (
          <section className="card">
            <h2>Daily Costs</h2>
            <div className="chart-box">
              <ResponsiveContainer width="100%" height={350}>
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
          </section>
        )}

        {/* ROTABLES USAGE */}
        {rotablesUsage.length > 0 && (
          <section className="card">
            <h2>Daily Rotables Usage</h2>
            <div className="chart-box">
              <ResponsiveContainer width="100%" height={350}>
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
          </section>
        )}

        {/* KPI GRID */}
        {rotablesUsage.length > 0 && (
          <section className="kpi-grid">
            {[
              { label: "Total FC Used ", value: totalFC, color: "#a78bfa" },
              { label: "Total BC Used ", value: totalBC, color: "#4ade80" },
              { label: "Total PE Used ", value: totalPE, color: "#facc15" },
              { label: "Total EC Used ", value: totalEC, color: "#fb923c" },
            ].map((k, i) => (
              <div key={i} className="kpi-card">
                <span className="kpi-label">{k.label}</span>
                <span className="kpi-value" style={{ color: k.color }}>
                  {k.value.toLocaleString()}
                </span>
              </div>
            ))}
          </section>
        )}

        {/* STOCK TABLE */}
        {finalStocks.length > 0 && (
          <section className="card">
            <h2>Final Airport Stocks</h2>
            <StockTable stocks={finalStocks} />
          </section>
        )}
      </main>

      {/* FOOTER */}
      <footer className="footer">
        Airline Rotables Simulator © {new Date().getFullYear()}
      </footer>
    </div>
  );
};

export default App;
