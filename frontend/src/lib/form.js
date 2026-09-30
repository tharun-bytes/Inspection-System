const MATERIALS = ["steel", "aluminum", "plastic", "brass", "composite"];
const SHIFTS = ["day", "evening", "night"];

const EMPTY_FORM = {
  part_serial: "",
  part_name: "",
  inspector: "",
  material: "steel",
  shift: "day",
  dimension_deviation_pct: "",
  surface_roughness_ra: "",
  torque_nm: "",
  temperature_c: "",
  vibration_mm_s: "",
  cycle_time_s: "",
  notes: "",
};

const NUMERIC_FIELDS = [
  ["dimension_deviation_pct", "Dimension deviation (%)", 0, 100, 0.01],
  ["surface_roughness_ra", "Surface roughness Ra", 0, 50, 0.01],
  ["torque_nm", "Torque (Nm)", 0, 400, 0.1],
  ["temperature_c", "Temperature (C)", -40, 250, 0.1],
  ["vibration_mm_s", "Vibration (mm/s)", 0, 60, 0.01],
  ["cycle_time_s", "Cycle time (s)", 0, 600, 0.1],
];

export { EMPTY_FORM, MATERIALS, NUMERIC_FIELDS, SHIFTS };

export function validateForm(form) {
  const errors = {};

  if (!form.part_serial.trim()) errors.part_serial = "Serial is required";
  if (!form.part_name.trim()) errors.part_name = "Part name is required";
  if (!form.inspector.trim()) errors.inspector = "Inspector is required";

  NUMERIC_FIELDS.forEach(([name, label, min, max]) => {
    if (form[name] === "") {
      errors[name] = `${label} is required`;
      return;
    }
    const value = Number(form[name]);
    if (Number.isNaN(value)) {
      errors[name] = `${label} must be a number`;
    } else if (value < min || value > max) {
      errors[name] = `${label} must be between ${min} and ${max}`;
    }
  });

  return errors;
}

export function toPayload(form) {
  const payload = {
    part_serial: form.part_serial.trim(),
    part_name: form.part_name.trim(),
    inspector: form.inspector.trim(),
    material: form.material,
    shift: form.shift,
    notes: form.notes.trim() ? form.notes.trim() : null,
  };
  NUMERIC_FIELDS.forEach(([name]) => {
    payload[name] = Number(form[name]);
  });
  return payload;
}
