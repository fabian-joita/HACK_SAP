import React, { useState, useMemo } from "react";

interface Stock {
  name: string;
  FC: number;
  BC: number;
  PE: number;
  EC: number;
}

interface Props {
  stocks: Stock[];
}

/* ----------------- UTIL: COLOR CODING ---------------- */
const getColor = (value: number) => {
  if (value < 60) return "#ef4444"; // red
  if (value < 120) return "#facc15"; // yellow
  return "#4ade80"; // green
};

const StockTable: React.FC<Props> = ({ stocks }) => {
  /* ----------------- SEARCH STATE ---------------- */
  const [search, setSearch] = useState("");

  /* ----------------- SORTING STATE ---------------- */
  const [sortColumn, setSortColumn] = useState<keyof Stock | "">("");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

  /* ----------------- PAGINATION ---------------- */
  const [page, setPage] = useState(1);
  const pageSize = 15;

  /* ----------------- SORT HANDLER ---------------- */
  const handleSort = (column: keyof Stock) => {
    if (sortColumn === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortOrder("asc");
    }
  };

  /* ----------------- FILTER + SORT + PAGE ---------------- */
  const filtered = useMemo(() => {
    let data = [...stocks];

    // SEARCH FILTER
    if (search.trim() !== "") {
      data = data.filter((s) =>
        s.name.toLowerCase().includes(search.toLowerCase())
      );
    }

    // SORTING
    if (sortColumn) {
      data.sort((a, b) => {
        const v1 = a[sortColumn];
        const v2 = b[sortColumn];
        if (typeof v1 === "string") {
          return sortOrder === "asc"
            ? v1.localeCompare(v2 as string)
            : (v2 as string).localeCompare(v1);
        }
        return sortOrder === "asc" ? v1 - (v2 as number) : (v2 as number) - v1;
      });
    }

    return data;
  }, [stocks, search, sortColumn, sortOrder]);

  const totalPages = Math.ceil(filtered.length / pageSize);

  const pageData = filtered.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div className="stock-wrapper">
      {/* ----------------- SEARCH BAR ---------------- */}
      <input
        type="text"
        placeholder="Search airport..."
        className="stock-search"
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1);
        }}
      />

      <table className="stock-table">
        <thead>
          <tr>
            {["name", "FC", "BC", "PE", "EC"].map((col) => (
              <th key={col} onClick={() => handleSort(col as keyof Stock)}>
                {col === "name" ? "Airport" : col}
                {sortColumn === col && (
                  <span className="sort-icon">
                    {sortOrder === "asc" ? " ▲" : " ▼"}
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {pageData.map((s, i) => (
            <tr key={i} className={i % 2 === 0 ? "row-even" : "row-odd"}>
              <td className="stock-airport">{s.name}</td>

              {/* FC */}
              <td>
                <div className="progress-cell">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${Math.min(s.FC, 200)}px`,
                      background: getColor(s.FC),
                    }}
                  />
                  <span>{s.FC}</span>
                </div>
              </td>

              {/* BC */}
              <td>
                <div className="progress-cell">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${Math.min(s.BC, 200)}px`,
                      background: getColor(s.BC),
                    }}
                  />
                  <span>{s.BC}</span>
                </div>
              </td>

              {/* PE */}
              <td>
                <div className="progress-cell">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${Math.min(s.PE, 200)}px`,
                      background: getColor(s.PE),
                    }}
                  />
                  <span>{s.PE}</span>
                </div>
              </td>

              {/* EC */}
              <td className={s.EC < 60 ? "low-stock" : ""}>
                <div className="progress-cell">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${Math.min(s.EC, 200)}px`,
                      background: getColor(s.EC),
                    }}
                  />
                  <span>{s.EC}</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* ----------------- PAGINATION ---------------- */}
      <div className="pagination">
        <button
          disabled={page === 1}
          onClick={() => setPage(page - 1)}
          className="page-btn"
        >
          Prev
        </button>

        <span className="page-info">
          Page {page} / {totalPages}
        </span>

        <button
          disabled={page === totalPages}
          onClick={() => setPage(page + 1)}
          className="page-btn"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default StockTable;
