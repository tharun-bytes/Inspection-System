const DEFAULT_BASE_URL = "http://localhost:8000";

export const API_BASE_URL =
  (import.meta.env && import.meta.env.VITE_API_URL) || DEFAULT_BASE_URL;

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, { method = "GET", body, signal } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      signal,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (cause) {
    if (cause.name === "AbortError") throw cause;
    throw new ApiError("Cannot reach the backend API. Is it running?", 0);
  }

  if (response.status === 204) return null;

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const detail =
      (payload && (payload.detail || payload.message)) || response.statusText;
    throw new ApiError(describe(detail), response.status);
  }

  return payload;
}

function describe(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : "value";
        return `${field}: ${item.msg}`;
      })
      .join("; ");
  }
  return "Request failed";
}

function toQuery(params) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, value);
    }
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function fetchHealth(options) {
  return request("/health", options);
}

export function fetchStats(options) {
  return request("/api/inspections/stats", options);
}

export function fetchInspections(filters = {}, options) {
  return request(`/api/inspections${toQuery(filters)}`, options);
}

export function createInspection(payload, options) {
  return request("/api/inspections", { ...options, method: "POST", body: payload });
}

export function reinspect(id, options) {
  return request(`/api/inspections/${id}/reinspect`, {
    ...options,
    method: "POST",
  });
}

export function deleteInspection(id, options) {
  return request(`/api/inspections/${id}`, { ...options, method: "DELETE" });
}
