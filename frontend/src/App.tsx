import React, { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from "recharts";

type DailyCost = {
  day: number;
  endOfDayCost: number;
  avgCost: number;
};

type RotablesUsage = {
  day: number;
  FC: number;
  BC: number;
  PE: number;
  EC: number;
};

const App: React.FC = () => {
  const [dailyCosts, setDailyCosts] = useState<DailyCost[]>([]);
  const [rotablesUsage, setRotablesUsage] = useState<RotablesUsage[]>([]);
  const [loading, setLoading] = useState(false);

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/run-main");
      const data = await res.json();
      if (data.success) {
        setDailyCosts(data.dailySummary);
        setRotablesUsage(data.rotablesUsage);
      } else {
        console.error(data.error);
      }
    } catch (err) {
      console.error("Backend connection failed");
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial" }}>
      <h1>Simulation Dashboard</h1>
      <button onClick={runSimulation}>
        {loading ? "Running..." : "Run Simulation"}
      </button>

      {/* Daily Costs Chart */}
      {dailyCosts.length > 0 && (
        <>
          <h2>Daily Costs</h2>
          <LineChart
            width={800}
            height={400}
            data={dailyCosts}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="day"
              label={{ value: "Day", position: "insideBottomRight", offset: -5 }}
            />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="endOfDayCost" stroke="#8884d8" />
            <Line type="monotone" dataKey="avgCost" stroke="#82ca9d" />
          </LineChart>
        </>
      )}

      {/* Rotables Usage Chart */}
      {rotablesUsage.length > 0 && (
        <>
          <h2>Daily Rotables Usage</h2>
          <LineChart
            width={800}
            height={400}
            data={rotablesUsage}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="day"
              label={{ value: "Day", position: "insideBottomRight", offset: -5 }}
            />
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
    </div>
  );
};

export default App;
