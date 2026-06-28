export default function QueryHistory({
  items,
  onPick,
}: {
  items: string[];
  onPick: (sql: string) => void;
}) {
  if (items.length === 0) {
    return null;
  }
  return (
    <div className="history">
      <span className="history-title">Historial</span>
      <ul className="history-list">
        {items.map((sql, i) => (
          <li key={i}>
            <button
              className="history-item"
              onClick={() => onPick(sql)}
              title={sql}
            >
              {sql}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
