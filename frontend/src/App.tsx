import React, { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import StockTable from "./components/StockTable";

type DailyTotal = {
  day: number;
  dailyTotal: number;
};

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

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/run-main");
      const data = await res.json();
      if (data.success) {
        setDailyTotals(data.dailyTotals || []);
        setRotablesUsage(data.rotablesUsage || []);
        setFinalStocks(data.finalStocks || []);
      } else {
        console.error(data.error);
      }
    } catch (err) {
      console.error("Backend connection failed");
    }
    setLoading(false);
  };

  const totalCost = dailyTotals.reduce((sum, d) => sum + d.dailyTotal, 0);

  return (
    <div
      style={{
        padding: "2rem",
        fontFamily: "Arial",
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <h1>Simulation Dashboard</h1>

      <button
        onClick={runSimulation}
        style={{
          padding: "10px 20px",
          fontSize: "16px",
          cursor: "pointer",
          marginBottom: "20px",
        }}
      >
        {loading ? "Running..." : "Run Simulation"}
      </button>

      {dailyTotals.length > 0 && (
        <h2>
          Total Cost:{" "}
          <span style={{ color: "green" }}>{totalCost.toFixed(2)}</span>
        </h2>
      )}

      {dailyTotals.length > 0 && (
        <>
          <h2>Daily Costs</h2>
          <LineChart width={800} height={400} data={dailyTotals}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="dailyTotal" stroke="#ff0000" />
          </LineChart>
        </>
      )}

      {rotablesUsage.length > 0 && (
        <>
          <h2>Daily Rotables Usage</h2>
          <LineChart width={800} height={400} data={rotablesUsage}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="FC" stroke="#8884d8" />
            <Line type="monotone" dataKey="BC" stroke="#82ca9d" />
            <Line type="monotone" dataKey="PE" stroke="#ffc658" />
            <Line type="monotone" dataKey="EC" stroke="#ff7300" />
          </LineChart>
        </>
      )}

      {/* STOCK TABLE */}
      {finalStocks.length > 0 && (
        <div style={{ marginTop: "50px" }}>
          <StockTable stocks={finalStocks} />
        </div>
      )}
    </div>
  );
};

export default App;
