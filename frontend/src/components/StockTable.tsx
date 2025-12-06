import React from "react";

// Define the shape of a single stock item
interface Stock {
  name: string;
  FC: number;
  BC: number;
  PE: number;
  EC: number;
}

// Define the props for StockTable
interface StockTableProps {
  stocks: Stock[];
}

const StockTable: React.FC<StockTableProps> = ({ stocks }) => {
  return (
    <div>
      <h2>Stock Data</h2>
      <table border={1} cellPadding={5}>
        <thead>
          <tr>
            <th>Stock</th>
            <th>FC</th>
            <th>BC</th>
            <th>PE</th>
            <th>EC</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock, index) => (
            <tr key={index}>
              <td>{stock.name}</td>
              <td>{stock.FC}</td>
              <td>{stock.BC}</td>
              <td>{stock.PE}</td>
              <td>{stock.EC}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default StockTable;
