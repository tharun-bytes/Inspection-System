export default function StatsBar({ stats }) {
  if (!stats) return null;

  const severity = new Map(
    (stats.severity_breakdown || []).map((row) => [row.severity, row.count]),
  );
  const total = stats.total_inspections || 0;

  const cards = [
    { label: "Inspections", value: total, tone: "" },
    { label: "Critical", value: severity.get("critical") || 0, tone: "card--critical" },
    { label: "Major", value: severity.get("major") || 0, tone: "card--major" },
    { label: "Minor", value: severity.get("minor") || 0, tone: "card--minor" },
    {
      label: "Critical rate",
      value: `${Math.round((stats.critical_rate || 0) * 100)}%`,
      tone: "card--critical",
    },
    {
      label: "Avg confidence",
      value:
        stats.average_confidence == null
          ? "n/a"
          : `${Math.round(stats.average_confidence * 100)}%`,
      tone: "",
    },
  ];

  return (
    <section className="stats" aria-label="Summary">
      {cards.map((card) => (
        <div key={card.label} className={`card ${card.tone}`}>
          <span className="card__value">{card.value}</span>
          <span className="card__label">{card.label}</span>
        </div>
      ))}
    </section>
  );
}
