import React from "react";

interface Stock {
  name: string;
  FC: number;
  BC: number;
  PE: number;
  EC: number;
}

interface Props {
  stocks: Stock[];
  dark: boolean;
}

const StockTable: React.FC<Props> = ({ stocks, dark }) => {
  return (
    <div style={{ overflowX: "auto", borderRadius: "16px" }}>
      <table
        style={{
          width: "100%",
          minWidth: "600px",
          borderCollapse: "collapse",
          background: dark ? "#1c1f25" : "white",
          color: dark ? "white" : "black",
        }}
      >
        <thead>
          <tr style={{ background: dark ? "#2b2f36" : "#eee", height: "50px" }}>
            <th>Airport</th>
            <th>FC</th>
            <th>BC</th>
            <th>PE</th>
            <th>EC</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((s, index) => (
            <tr
              key={index}
              style={{
                background:
                  index % 2 === 0
                    ? dark
                      ? "#181b1f"
                      : "#fafafa"
                    : dark
                    ? "#14171b"
                    : "#f4f4f4",
                height: "48px",
              }}
            >
              <td style={{ padding: "12px", fontWeight: 600 }}>{s.name}</td>
              <td style={{ padding: "12px" }}>{s.FC}</td>
              <td style={{ padding: "12px" }}>{s.BC}</td>
              <td style={{ padding: "12px" }}>{s.PE}</td>
              <td
                style={{
                  padding: "12px",
                  fontWeight: s.EC < 60 ? 700 : 500,
                  color: s.EC < 60 ? "#ff6b6b" : "",
                }}
              >
                {s.EC}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default StockTable;
