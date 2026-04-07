import { useCallback, useEffect, useState } from "react";
import { fetchCalendarEvents } from "../api";

function formatDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export default function CalendarPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadEvents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchCalendarEvents();
      setEvents(data);
    } catch (err) {
      console.error("Failed to load events", err);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  return (
    <div>
      <div className="page-header">
        <h2>Calendar</h2>
        <button className="btn" onClick={loadEvents} disabled={loading}>
          Refresh
        </button>
      </div>

      {loading && <p style={{ color: "var(--text-muted)" }}>Loading events...</p>}

      {!loading && events.length === 0 && (
        <p style={{ color: "var(--text-muted)" }}>No events yet.</p>
      )}

      <div className="task-grid">
        {events.map((event) => (
          <div key={event.id} className="task-card">
            <h3>{event.title}</h3>
            <p className="task-desc">
              {formatDateTime(event.start_time)}
              {event.end_time ? ` - ${formatDateTime(event.end_time)}` : ""}
            </p>
            {event.description && <p className="task-desc">{event.description}</p>}
            <div className="task-meta">
              <span className="badge medium">
                {event.calendar_error ? "calendar" : event.source || "calendar"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
