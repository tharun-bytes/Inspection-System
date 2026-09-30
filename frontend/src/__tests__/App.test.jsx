import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";

const health = {
  status: "ok",
  database: "up",
  ai_service: "up",
  version: "0.1.0",
};

const stats = {
  total_inspections: 1,
  average_confidence: 0.9,
  severity_breakdown: [
    { severity: "minor", count: 1 },
    { severity: "major", count: 0 },
    { severity: "critical", count: 0 },
  ],
  status_breakdown: [{ status: "passed", count: 1 }],
  critical_rate: 0,
};

const inspection = {
  id: 1,
  part_serial: "SN-0001",
  part_name: "Drive Shaft",
  inspector: "alice",
  material: "steel",
  shift: "day",
  dimension_deviation_pct: 0.4,
  surface_roughness_ra: 0.6,
  torque_nm: 12,
  temperature_c: 28,
  vibration_mm_s: 0.9,
  cycle_time_s: 12,
  severity: "minor",
  confidence: 0.9,
  status: "passed",
  notes: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function jsonResponse(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: "status",
    text: () => Promise.resolve(JSON.stringify(body)),
  };
}

function routeFetch(overrides = {}) {
  return vi.fn(async (url, init = {}) => {
    const path = String(url).replace("http://localhost:8000", "");

    if (overrides[path]) return overrides[path](init);

    if (path.startsWith("/health")) return jsonResponse(health);
    if (path.includes("/stats")) return jsonResponse(stats);
    if (path.includes("/reinspect")) {
      return jsonResponse({ ...inspection, ai_warning: null });
    }
    if (init.method === "POST" && path === "/api/inspections") {
      return jsonResponse({ ...inspection, ai_warning: null }, 201);
    }
    if (init.method === "DELETE") return { ok: true, status: 204, text: () => Promise.resolve("") };
    if (path.startsWith("/api/inspections")) {
      return jsonResponse({ items: [inspection], total: 1, limit: 100, offset: 0 });
    }
    throw new Error(`Unhandled request: ${path}`);
  });
}

describe("App", () => {
  beforeEach(() => {
    global.fetch = routeFetch();
  });

  it("shows service health from the backend", async () => {
    render(<App />);
    expect(await screen.findByText("Database")).toBeInTheDocument();
    expect(screen.getAllByText("up").length).toBeGreaterThanOrEqual(2);
  });

  it("renders the dashboard summary", async () => {
    render(<App />);
    expect(await screen.findByText("Inspections")).toBeInTheDocument();
    expect(screen.getByText("Critical rate")).toBeInTheDocument();
  });

  it("lists existing inspections", async () => {
    render(<App />);
    expect(await screen.findByText("SN-0001")).toBeInTheDocument();
    expect(screen.getByText("Drive Shaft")).toBeInTheDocument();
  });

  it("refuses to submit an incomplete form", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("SN-0001");

    await user.click(screen.getByRole("button", { name: /create and predict/i }));

    expect(await screen.findByText("Serial is required")).toBeInTheDocument();
    expect(global.fetch).not.toHaveBeenCalledWith(
      expect.stringContaining("/api/inspections"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("submits a valid form and reports the AI verdict", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("SN-0001");

    await user.type(screen.getByLabelText(/part serial/i), "SN-0002");
    await user.type(screen.getByLabelText(/part name/i), "Gear");
    await user.type(screen.getByLabelText(/^inspector$/i), "bob");
    await user.type(screen.getByLabelText(/dimension deviation/i), "2");
    await user.type(screen.getByLabelText(/surface roughness/i), "1");
    await user.type(screen.getByLabelText(/torque/i), "20");
    await user.type(screen.getByLabelText(/temperature/i), "30");
    await user.type(screen.getByLabelText(/vibration/i), "1");
    await user.type(screen.getByLabelText(/cycle time/i), "12");

    await user.click(screen.getByRole("button", { name: /create and predict/i }));

    expect(await screen.findByRole("status")).toHaveTextContent(/minor/i);
  });

  it("surfaces the backend warning when the AI service is down", async () => {
    global.fetch = routeFetch({
      "/api/inspections": () =>
        jsonResponse(
          { ...inspection, severity: null, status: "pending", ai_warning: "AI service unreachable" },
          201,
        ),
    });
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("SN-0001");

    await user.type(screen.getByLabelText(/part serial/i), "SN-0003");
    await user.type(screen.getByLabelText(/part name/i), "Gear");
    await user.type(screen.getByLabelText(/^inspector$/i), "bob");
    await user.type(screen.getByLabelText(/dimension deviation/i), "2");
    await user.type(screen.getByLabelText(/surface roughness/i), "1");
    await user.type(screen.getByLabelText(/torque/i), "20");
    await user.type(screen.getByLabelText(/temperature/i), "30");
    await user.type(screen.getByLabelText(/vibration/i), "1");
    await user.type(screen.getByLabelText(/cycle time/i), "12");

    await user.click(screen.getByRole("button", { name: /create and predict/i }));

    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(/AI service was unavailable/i),
    );
  });

  it("warns when the backend itself is unreachable", async () => {
    global.fetch = vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    });
    render(<App />);
    expect(await screen.findByText(/Backend unreachable/i)).toBeInTheDocument();
  });
});
