import { useState, useEffect, useCallback } from "react";
import { fetchLogs } from "../api";

export default function LogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchLogs(null, 200);
      setLogs(data);
    } catch (err) {
      console.error("Failed to load logs:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  const formatTime = (iso) => {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  };

  const formatJson = (obj) => {
    if (!obj || Object.keys(obj).length === 0) return "—";
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return String(obj);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>Execution Logs</h2>
        <button className="btn" onClick={loadLogs} disabled={loading}>
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="loading">
          <div className="spinner" /> Loading logs...
        </div>
      ) : logs.length === 0 ? (
        <div className="empty-state">
          <h3>No execution logs</h3>
          <p>Interact with the AI chat to generate agent execution traces.</p>
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table className="logs-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Agent</th>
                <th>Tool</th>
                <th>Status</th>
                <th>Input</th>
                <th>Output</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ whiteSpace: "nowrap" }}>{formatTime(log.timestamp)}</td>
                  <td>
                    <span
                      className="agent-badge"
                      style={{
                        background: "var(--primary)",
                        color: "#fff",
                        padding: "2px 8px",
                        borderRadius: 4,
                        fontSize: 11,
                        fontWeight: 600,
                      }}
                    >
                      {log.agent_name}
                    </span>
                  </td>
                  <td>
                    <code>{log.tool_name}</code>
                  </td>
                  <td>
                    <span className={`status-dot ${log.success ? "success" : "error"}`} />
                    {log.success ? "OK" : "Error"}
                  </td>
                  <td>
                    <details>
                      <summary style={{ cursor: "pointer", fontSize: 12 }}>View</summary>
                      <pre
                        style={{
                          fontSize: 11,
                          marginTop: 4,
                          maxWidth: 300,
                          overflow: "auto",
                        }}
                      >
                        {formatJson(log.input)}
                      </pre>
                    </details>
                  </td>
                  <td>
                    <details>
                      <summary style={{ cursor: "pointer", fontSize: 12 }}>View</summary>
                      <pre
                        style={{
                          fontSize: 11,
                          marginTop: 4,
                          maxWidth: 300,
                          overflow: "auto",
                        }}
                      >
                        {log.error_message || formatJson(log.output)}
                      </pre>
                    </details>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
