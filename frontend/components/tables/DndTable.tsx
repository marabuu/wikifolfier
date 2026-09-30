export interface Column {
  header: string;
  /** Column rendered centered + nowrap, like numeric Wikidot tables. */
  numeric?: boolean;
}

export interface TableRow {
  cells: (string | number)[];
  /** Row header cell (first column, bold, grey background). */
  header?: boolean;
}

/**
 * Reusable Wikidot-style table: bordered, collapsed, dense, caption above.
 */
export function DndTable({
  caption,
  columns,
  rows,
  striped = false,
}: {
  caption?: string;
  columns: Column[];
  rows: TableRow[];
  striped?: boolean;
}) {
  return (
    <div className="table-wrapper">
      <table className={`dnd-table${striped ? ' dnd-table--striped' : ''}`}>
        {caption && <caption>{caption}</caption>}
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.header} scope="col" className={column.numeric ? 'num' : undefined}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {row.cells.map((cell, cellIndex) => {
                const isHeader = row.header && cellIndex === 0;
                if (isHeader) {
                  return (
                    <th key={cellIndex} scope="row">
                      {cell}
                    </th>
                  );
                }
                return (
                  <td key={cellIndex} className={columns[cellIndex]?.numeric ? 'num' : undefined}>
                    {cell}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}