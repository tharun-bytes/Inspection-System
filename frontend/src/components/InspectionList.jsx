import { Fragment, useState } from "react";
import SeverityBadge from "./SeverityBadge";

const STATUS_OPTIONS = ["", "pending", "passed", "failed", "review"];
const SEVERITY_OPTIONS = ["", "minor", "major", "critical"];

export default function InspectionList({
  page,
  filters,
  onFilterChange,
  onReinspect,
  onDelete,
  busyId,
}) {
  const [expanded, setExpanded] = useState(null);

  const items = (page && page.items) || [];

  return (
    <section className="list">
      <div className="list__header">
        <h2>Inspections {page ? `(${page.total})` : ""}</h2>
        <div className="list__filters">
          <label>
            Status
            <select
              value={filters.status}
              onChange={(event) => onFilterChange({ ...filters, status: event.target.value })}
            >
              {STATUS_OPTIONS.map((value) => (
                <option key={value} value={value}>
                  {value || "All"}
                </option>
              ))}
            </select>
          </label>
          <label>
            Severity
            <select
              value={filters.severity}
              onChange={(event) => onFilterChange({ ...filters, severity: event.target.value })}
            >
              {SEVERITY_OPTIONS.map((value) => (
                <option key={value} value={value}>
                  {value || "All"}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {items.length === 0 ? (
        <p className="list__empty">No inspections match the current filters.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Serial</th>
              <th>Part</th>
              <th>Inspector</th>
              <th>Shift</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Confidence</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <Fragment key={item.id}>
                <tr key={item.id}>
                  <td>{item.part_serial}</td>
                  <td>{item.part_name}</td>
                  <td>{item.inspector}</td>
                  <td>{item.shift}</td>
                  <td>
                    <SeverityBadge value={item.severity} />
                  </td>
                  <td>
                    <SeverityBadge value={item.status} />
                  </td>
                  <td>
                    {item.confidence == null ? "n/a" : `${Math.round(item.confidence * 100)}%`}
                  </td>
                  <td className="list__actions">
                    <button
                      type="button"
                      onClick={() => onReinspect(item.id)}
                      disabled={busyId === item.id}
                    >
                      Re-predict
                    </button>
                    <button type="button" onClick={() => onDelete(item.id)}>
                      Delete
                    </button>
                    <button
                      type="button"
                      onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                    >
                      {expanded === item.id ? "Hide" : "Details"}
                    </button>
                  </td>
                </tr>
                {expanded === item.id && (
                  <tr className="list__detail">
                    <td colSpan="8">
                      <dl>
                        <div>
                          <dt>Material</dt>
                          <dd>{item.material}</dd>
                        </div>
                        <div>
                          <dt>Dimension deviation</dt>
                          <dd>{item.dimension_deviation_pct}%</dd>
                        </div>
                        <div>
                          <dt>Surface roughness</dt>
                          <dd>{item.surface_roughness_ra} Ra</dd>
                        </div>
                        <div>
                          <dt>Torque</dt>
                          <dd>{item.torque_nm} Nm</dd>
                        </div>
                        <div>
                          <dt>Temperature</dt>
                          <dd>{item.temperature_c} C</dd>
                        </div>
                        <div>
                          <dt>Vibration</dt>
                          <dd>{item.vibration_mm_s} mm/s</dd>
                        </div>
                        <div>
                          <dt>Cycle time</dt>
                          <dd>{item.cycle_time_s} s</dd>
                        </div>
                        <div>
                          <dt>Notes</dt>
                          <dd>{item.notes || "-"}</dd>
                        </div>
                      </dl>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
