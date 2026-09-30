import { EMPTY_FORM, toPayload, validateForm } from "../lib/form";

const valid = {
  ...EMPTY_FORM,
  part_serial: "SN-1",
  part_name: "Drive Shaft",
  inspector: "alice",
  dimension_deviation_pct: "1.2",
  surface_roughness_ra: "0.8",
  torque_nm: "20",
  temperature_c: "35",
  vibration_mm_s: "1.1",
  cycle_time_s: "15",
};

describe("validateForm", () => {
  it("accepts a complete form", () => {
    expect(validateForm(valid)).toEqual({});
  });

  it.each([
    ["part_serial", "Serial is required"],
    ["part_name", "Part name is required"],
    ["inspector", "Inspector is required"],
  ])("requires %s", (field, message) => {
    const errors = validateForm({ ...valid, [field]: "   " });
    expect(errors[field]).toBe(message);
  });

  it.each([
    "dimension_deviation_pct",
    "surface_roughness_ra",
    "torque_nm",
    "temperature_c",
    "vibration_mm_s",
    "cycle_time_s",
  ])("requires a value for %s", (field) => {
    const errors = validateForm({ ...valid, [field]: "" });
    expect(errors[field]).toMatch(/required/i);
  });

  it("rejects a non-numeric measurement", () => {
    const errors = validateForm({ ...valid, torque_nm: "high" });
    expect(errors.torque_nm).toMatch(/must be a number/i);
  });

  it("rejects a measurement above the allowed maximum", () => {
    const errors = validateForm({ ...valid, torque_nm: "9999" });
    expect(errors.torque_nm).toMatch(/between 0 and 400/i);
  });

  it("accepts a negative temperature but not a negative deviation", () => {
    expect(validateForm({ ...valid, temperature_c: "-10" })).toEqual({});
    expect(validateForm({ ...valid, dimension_deviation_pct: "-1" })).toMatchObject({
      dimension_deviation_pct: expect.stringMatching(/between 0 and 100/i),
    });
  });
});

describe("toPayload", () => {
  it("trims text and coerces numbers", () => {
    const payload = toPayload({ ...valid, part_serial: "  SN-9  " });

    expect(payload.part_serial).toBe("SN-9");
    expect(payload.torque_nm).toBe(20);
    expect(payload.dimension_deviation_pct).toBeCloseTo(1.2);
  });

  it("sends null for empty notes", () => {
    expect(toPayload({ ...valid, notes: "   " }).notes).toBeNull();
  });

  it("keeps supplied notes", () => {
    expect(toPayload({ ...valid, notes: " recalibrated " }).notes).toBe("recalibrated");
  });

  it("carries material and shift through", () => {
    const payload = toPayload({ ...valid, material: "brass", shift: "night" });

    expect(payload.material).toBe("brass");
    expect(payload.shift).toBe("night");
  });
});
