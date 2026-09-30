import { useState } from "react";
import { EMPTY_FORM, MATERIALS, NUMERIC_FIELDS, SHIFTS, toPayload, validateForm } from "../lib/form";

export default function InspectionForm({ onCreate, submitting }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});

  function update(field) {
    return (event) => {
      const { value } = event.target;
      setForm((previous) => ({ ...previous, [field]: value }));
      setErrors((previous) => {
        if (!previous[field]) return previous;
        const next = { ...previous };
        delete next[field];
        return next;
      });
    };
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const found = validateForm(form);
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    const created = await onCreate(toPayload(form));
    if (created) {
      setForm(EMPTY_FORM);
      setErrors({});
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit} noValidate>
      <h2>New inspection</h2>

      <div className="form__row">
        <label>
          Part serial
          <input
            name="part_serial"
            value={form.part_serial}
            onChange={update("part_serial")}
            aria-invalid={Boolean(errors.part_serial)}
          />
          {errors.part_serial && <span className="error">{errors.part_serial}</span>}
        </label>

        <label>
          Part name
          <input
            name="part_name"
            value={form.part_name}
            onChange={update("part_name")}
            aria-invalid={Boolean(errors.part_name)}
          />
          {errors.part_name && <span className="error">{errors.part_name}</span>}
        </label>

        <label>
          Inspector
          <input
            name="inspector"
            value={form.inspector}
            onChange={update("inspector")}
            aria-invalid={Boolean(errors.inspector)}
          />
          {errors.inspector && <span className="error">{errors.inspector}</span>}
        </label>
      </div>

      <div className="form__row">
        <label>
          Material
          <select name="material" value={form.material} onChange={update("material")}>
            {MATERIALS.map((material) => (
              <option key={material} value={material}>
                {material}
              </option>
            ))}
          </select>
        </label>

        <label>
          Shift
          <select name="shift" value={form.shift} onChange={update("shift")}>
            {SHIFTS.map((shift) => (
              <option key={shift} value={shift}>
                {shift}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="form__row form__row--wrap">
        {NUMERIC_FIELDS.map(([name, label, min, max, step]) => (
          <label key={name}>
            {label}
            <input
              name={name}
              type="number"
              min={min}
              max={max}
              step={step}
              value={form[name]}
              onChange={update(name)}
              aria-invalid={Boolean(errors[name])}
            />
            {errors[name] && <span className="error">{errors[name]}</span>}
          </label>
        ))}
      </div>

      <label>
        Notes (optional)
        <textarea name="notes" rows="2" value={form.notes} onChange={update("notes")} />
      </label>

      <button type="submit" disabled={submitting}>
        {submitting ? "Predicting..." : "Create and predict"}
      </button>
    </form>
  );
}
