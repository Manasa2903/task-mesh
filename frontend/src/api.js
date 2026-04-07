const BASE = "";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

// Chat
export const sendMessage = (message, sessionId) =>
  request("/chat", {
    method: "POST",
    body: JSON.stringify({ message, session_id: sessionId }),
  });

export const fetchChatHistory = (sessionId, limit = 100) => {
  const params = new URLSearchParams();
  if (sessionId) params.set("session_id", sessionId);
  if (limit) params.set("limit", limit);
  const qs = params.toString();
  return request(`/chat/history${qs ? `?${qs}` : ""}`);
};

export const clearChatHistory = (sessionId) => {
  const params = new URLSearchParams();
  if (sessionId) params.set("session_id", sessionId);
  const qs = params.toString();
  return request(`/chat/history${qs ? `?${qs}` : ""}`, { method: "DELETE" });
};

// Tasks
export const fetchTasks = (status) =>
  request(`/tasks${status ? `?status=${status}` : ""}`);

export const createTask = (data) =>
  request("/tasks", { method: "POST", body: JSON.stringify(data) });

export const updateTask = (id, data) =>
  request(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) });

export const deleteTask = (id) => request(`/tasks/${id}`, { method: "DELETE" });

// Calendar
export const fetchCalendarEvents = (date, maxResults = 100) => {
  const params = new URLSearchParams();
  if (date) params.set("date", date);
  if (maxResults) params.set("max_results", maxResults);
  const qs = params.toString();
  return request(`/calendar/events${qs ? `?${qs}` : ""}`);
};

// Notes
export const fetchNotes = () => request("/notes");

export const createNote = (data) =>
  request("/notes", { method: "POST", body: JSON.stringify(data) });

export const updateNote = (id, data) =>
  request(`/notes/${id}`, { method: "PATCH", body: JSON.stringify(data) });

export const deleteNote = (id) => request(`/notes/${id}`, { method: "DELETE" });

// Logs
export const fetchLogs = (sessionId, limit = 100) => {
  const params = new URLSearchParams();
  if (sessionId) params.set("session_id", sessionId);
  if (limit) params.set("limit", limit);
  const qs = params.toString();
  return request(`/logs${qs ? `?${qs}` : ""}`);
};
