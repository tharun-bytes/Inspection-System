import { useCallback, useEffect, useState } from "react";
import HealthBar from "./components/HealthBar";
import InspectionForm from "./components/InspectionForm";
import InspectionList from "./components/InspectionList";
import StatsBar from "./components/StatsBar";
import {
  ApiError,
  createInspection,
  deleteInspection,
  fetchHealth,
  fetchInspections,
  fetchStats,
  reinspect,
} from "./lib/api";

const EMPTY_FILTERS = { status: "", severity: "" };

export default function App() {
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState(null);
  const [stats, setStats] = useState(null);
  const [page, setPage] = useState(null);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [notice, setNotice] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [busyId, setBusyId] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const [statsResult, listResult] = await Promise.all([
        fetchStats(),
        fetchInspections({ ...filters, limit: 100 }),
      ]);
      setStats(statsResult);
      setPage(listResult);
      setError(null);
    } catch (cause) {
      setError(cause.message);
    }
  }, [filters]);

  useEffect(() => {
    let cancelled = false;

    fetchHealth()
      .then((result) => {
        if (!cancelled) {
          setHealth(result);
          setHealthError(null);
        }
      })
      .catch((cause) => {
        if (!cancelled) setHealthError(cause.message);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleCreate(payload) {
    setSubmitting(true);
    setNotice(null);
    setError(null);
    try {
      const created = await createInspection(payload);
      setNotice(
        created.ai_warning
          ? `Saved ${created.part_serial} but the AI service was unavailable (${created.ai_warning}).`
          : `Saved ${created.part_serial}: ${created.severity} (${Math.round(created.confidence * 100)}% confidence).`,
      );
      await refresh();
      return created;
    } catch (cause) {
      setError(
        cause instanceof ApiError ? cause.message : "Could not save the inspection.",
      );
      return null;
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReinspect(id) {
    setBusyId(id);
    setNotice(null);
    try {
      const result = await reinspect(id);
      setNotice(
        result.ai_warning
          ? `AI still unavailable: ${result.ai_warning}`
          : `Re-predicted ${result.part_serial}: ${result.severity}.`,
      );
      await refresh();
    } catch (cause) {
      setError(cause.message);
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(id) {
    setBusyId(id);
    try {
      await deleteInspection(id);
      setNotice(`Deleted inspection ${id}.`);
      await refresh();
    } catch (cause) {
      setError(cause.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <main className="app">
      <header className="app__header">
        <h1>Inspection System</h1>
        <p>Quality inspection with AI-assisted severity grading.</p>
      </header>

      <HealthBar health={health} error={healthError} />
      <StatsBar stats={stats} />

      {notice && (
        <div className="notice" role="status">
          {notice}
        </div>
      )}
      {error && (
        <div className="notice notice--error" role="alert">
          {error}
        </div>
      )}

      <InspectionForm onCreate={handleCreate} submitting={submitting} />

      <InspectionList
        page={page}
        filters={filters}
        onFilterChange={setFilters}
        onReinspect={handleReinspect}
        onDelete={handleDelete}
        busyId={busyId}
      />
    </main>
  );
}
