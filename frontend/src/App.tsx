import React from "react";
import StockTable from "./components/StockTable"; // make sure path is correct

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

const stocks: Stock[] = [
  { code: "YCCY", FC: 57, BC: 93, PE: 103, EC: 174 },
  { code: "DHXR", FC: 96, BC: 17, PE: 48, EC: 282 },
];

const loadDecisions: FlightLoad[] = [
  { flightId: "835f46d4-aa03-4a31-8ba5-3bdcf63b1252", FC: 4, BC: 13, PE: 14, EC: 111 },
  { flightId: "79b3a28a-6d4d-4db8-ad41-69a64e536cae", FC: 3, BC: 28, PE: 6, EC: 156 },
];

const landings: Landing[] = [
  { flightId: "88105f49-fef3-424a-8003-1894a0f4bdb0", used: { first: 2, business: 1, premium_economy: 2, economy: 57 }, destination: "FQCG" },
  { flightId: "9b07f95c-b5b7-4b48-b431-dc47a92f7b7f", used: { first: 14, business: 58, premium_economy: 21, economy: 311 }, destination: "GEJJ" },
];

const App: React.FC = () => {
  // Map Stock[] to match StockTable props (name instead of code)
  const tableStocks = stocks.map(stock => ({
    name: stock.code,
    FC: stock.FC,
    BC: stock.BC,
    PE: stock.PE,
    EC: stock.EC,
  }));

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial" }}>
      <h1>Stock Overview</h1>
      <StockTable stocks={tableStocks} />

      <h1>Load Decisions</h1>
      <ul>
        {loadDecisions.map(load => (
          <li key={load.flightId}>
            Flight: {load.flightId} — FC={load.FC} BC={load.BC} PE={load.PE} EC={load.EC}
          </li>
        ))}
      </ul>

      <h1>Landings</h1>
      <ul>
        {landings.map(landing => (
          <li key={landing.flightId}>
            Flight: {landing.flightId} → {landing.destination} — Used: FC={landing.used.first} BC={landing.used.business} PE={landing.used.premium_economy} EC={landing.used.economy}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default App;
