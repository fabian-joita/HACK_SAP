import React, { useState } from "react";
import StockTable from "./components/StockTable";

type Stock = {
  code: string;
  FC: number;
  BC: number;
  PE: number;
  EC: number;
};

type FlightLoad = {
  flightId: string;
  FC: number;
  BC: number;
  PE: number;
  EC: number;
};

type Landing = {
  flightId: string;
  used: { first: number; business: number; premium_economy: number; economy: number };
  destination: string;
};

const App: React.FC = () => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loadDecisions, setLoadDecisions] = useState<FlightLoad[]>([]);
  const [landings, setLandings] = useState<Landing[]>([]);
  const [loading, setLoading] = useState(false);
  const [rawOutput, setRawOutput] = useState("");

  // ----------------------------
  // PARSE BACKEND OUTPUT (Regex)
  // ----------------------------
  const parseOutput = (output: string) => {
    setRawOutput(output);

    // STOCKS
    const stockMatches = [...output.matchAll(/STOCK\[(\w+)\]\s+FC=(\d+)\s+BC=(\d+)\s+PE=(\d+)\s+EC=(\d+)/g)];
    const parsedStocks: Stock[] = stockMatches.map(m => ({
      code: m[1],
      FC: Number(m[2]),
      BC: Number(m[3]),
      PE: Number(m[4]),
      EC: Number(m[5]),
    }));

    // LOAD DECISIONS
    const loadMatches = [...output.matchAll(
      /LOAD Flight=([a-f0-9\-]+)\s+FC=(\d+)\s+BC=(\d+)\s+PE=(\d+)\s+EC=(\d+)/gi
    )];
    const parsedLoads: FlightLoad[] = loadMatches.map(m => ({
      flightId: m[1],
      FC: Number(m[2]),
      BC: Number(m[3]),
      PE: Number(m[4]),
      EC: Number(m[5]),
    }));

    // LANDINGS
    const landingMatches = [...output.matchAll(
      /LANDING Flight=([a-f0-9\-]+)\s+Used=PerClassAmount\(first=(\d+), business=(\d+), premium_economy=(\d+), economy=(\d+)\)\s+→\s+(\w+)/gi
    )];
    const parsedLandings: Landing[] = landingMatches.map(m => ({
      flightId: m[1],
      used: {
        first: Number(m[2]),
        business: Number(m[3]),
        premium_economy: Number(m[4]),
        economy: Number(m[5]),
      },
      destination: m[6],
    }));

    setStocks(parsedStocks);
    setLoadDecisions(parsedLoads);
    setLandings(parsedLandings);
  };

  // ----------------------------
  // CALL BACKEND
  // ----------------------------
const runSimulation = async () => {
  setLoading(true);

  try {
    const res = await fetch("http://127.0.0.1:8000/run-main");

    console.log("Response status:", res.status);   // new
    console.log("Response headers:", res.headers); // new

    const text = await res.text();  // read raw text
    console.log("Raw response text:", text);      // new

    const data = JSON.parse(text);  // parse manually
    if (data.success) {
      parseOutput(data.output);
    } else {
      setRawOutput("ERROR:\n" + data.error);
    }
  } catch (err) {
    setRawOutput("Failed to connect to backend:\n" + String(err));
  }

  setLoading(false);
};

  const tableStocks = stocks.map(stock => ({
    name: stock.code,
    FC: stock.FC,
    BC: stock.BC,
    PE: stock.PE,
    EC: stock.EC,
  }));

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial" }}>
      <h1>Rotables Dashboard</h1>

      {/* RUN BACKEND BUTTON */}
      <button
        onClick={runSimulation}
        style={{
          padding: "10px 20px",
          fontSize: "16px",
          cursor: "pointer",
          marginBottom: "20px"
        }}
      >
        {loading ? "Running Simulation..." : "Run Simulation"}
      </button>

      {/* STOCK TABLE */}
      <h2>Stock Overview</h2>
      <StockTable stocks={tableStocks} />

      {/* LOAD DECISIONS */}
      <h2>Load Decisions</h2>
      <ul>
        {loadDecisions.map(load => (
          <li key={load.flightId}>
            Flight {load.flightId} — FC={load.FC}, BC={load.BC}, PE={load.PE}, EC={load.EC}
          </li>
        ))}
      </ul>

      {/* LANDINGS */}
      <h2>Landings</h2>
      <ul>
        {landings.map(landing => (
          <li key={landing.flightId}>
            Flight {landing.flightId} → {landing.destination} — 
            Used: FC={landing.used.first}, BC={landing.used.business}, PE={landing.used.premium_economy}, EC={landing.used.economy}
          </li>
        ))}
      </ul>

      {/* RAW BACKEND OUTPUT */}
      <h2>Raw Backend Output</h2>
      <pre
        style={{
          background: "#eee",
          padding: "1rem",
          whiteSpace: "pre-wrap",
          maxHeight: "400px",
          overflowY: "scroll"
        }}
      >
        {rawOutput}
      </pre>
    </div>
  );
};

export default App;
