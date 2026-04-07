import { Routes, Route, NavLink } from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import TasksPage from "./pages/TasksPage";
import LogsPage from "./pages/LogsPage";
import CalendarPage from "./pages/CalendarPage";
import NotesPage from "./pages/NotesPage";

export default function App() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <h1>
          <span>⬡</span> TaskMesh
        </h1>
        <NavLink
          to="/"
          className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          end
        >
          💬 Chat
        </NavLink>
        <NavLink
          to="/tasks"
          className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
        >
          ✅ Tasks
        </NavLink>
        <NavLink
          to="/calendar"
          className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
        >
          📅 Calendar
        </NavLink>
        <NavLink
          to="/notes"
          className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
        >
          📝 Notes
        </NavLink>
        <NavLink
          to="/logs"
          className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
        >
          📋 Execution Logs
        </NavLink>
      </aside>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/tasks" element={<TasksPage />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/notes" element={<NotesPage />} />
          <Route path="/logs" element={<LogsPage />} />
        </Routes>
      </main>
    </div>
  );
}
