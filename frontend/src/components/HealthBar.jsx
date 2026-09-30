export default function HealthBar({ health, error }) {
  if (error) {
    return (
      <div className="health health--down" role="alert">
        <strong>Backend unreachable.</strong> Start it on port 8000 and reload.
      </div>
    );
  }

  if (!health) {
    return <div className="health">Checking service health...</div>;
  }

  const aiUp = health.ai_service === "up";
  const dbUp = health.database === "up";

  return (
    <div className={`health ${dbUp && aiUp ? "health--ok" : "health--warn"}`}>
      <span className="health__item">
        Backend <strong>v{health.version}</strong>
      </span>
      <span className="health__item">
        Database{" "}
        <strong className={dbUp ? "ok" : "bad"}>{health.database}</strong>
      </span>
      <span className="health__item">
        AI service{" "}
        <strong className={aiUp ? "ok" : "bad"}>{health.ai_service}</strong>
      </span>
    </div>
  );
}
