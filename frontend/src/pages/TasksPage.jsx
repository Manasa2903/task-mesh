import { useState, useEffect, useCallback } from "react";
import { fetchTasks, createTask, updateTask, deleteTask } from "../api";

export default function TasksPage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({
    title: "",
    description: "",
    due_date: "",
    priority: "medium",
  });

  const loadTasks = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchTasks();
      setTasks(data);
    } catch (err) {
      console.error("Failed to load tasks:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    try {
      await createTask({
        title: form.title,
        description: form.description,
        due_date: form.due_date || null,
        priority: form.priority,
      });
      setForm({ title: "", description: "", due_date: "", priority: "medium" });
      setShowModal(false);
      loadTasks();
    } catch (err) {
      console.error("Failed to create task:", err);
    }
  };

  const handleStatusToggle = async (task) => {
    const nextStatus = task.status === "done" ? "pending" : "done";
    try {
      await updateTask(task.id, { status: nextStatus });
      loadTasks();
    } catch (err) {
      console.error("Failed to update task:", err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteTask(id);
      loadTasks();
    } catch (err) {
      console.error("Failed to delete task:", err);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>Tasks</h2>
        <button className="btn" onClick={() => setShowModal(true)}>
          + New Task
        </button>
      </div>

      {loading ? (
        <div className="loading">
          <div className="spinner" /> Loading tasks...
        </div>
      ) : tasks.length === 0 ? (
        <div className="empty-state">
          <h3>No tasks yet</h3>
          <p>Create a task or ask the AI assistant to add one for you.</p>
        </div>
      ) : (
        <div className="task-grid">
          {tasks.map((task) => (
            <div key={task.id} className="task-card">
              <h3>{task.title}</h3>
              <div className="task-meta">
                <span className={`badge ${task.status}`}>{task.status}</span>
                <span className={`badge ${task.priority}`}>{task.priority}</span>
                {task.due_date && (
                  <span style={{ color: "var(--text-muted)" }}>Due: {task.due_date}</span>
                )}
              </div>
              {task.description && <p className="task-desc">{task.description}</p>}
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button
                  className="btn-secondary"
                  style={{ fontSize: 12, padding: "6px 12px" }}
                  onClick={() => handleStatusToggle(task)}
                >
                  {task.status === "done" ? "Reopen" : "Complete"}
                </button>
                <button
                  className="btn-secondary"
                  style={{ fontSize: 12, padding: "6px 12px", color: "var(--danger)" }}
                  onClick={() => handleDelete(task.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>New Task</h3>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Title</label>
                <input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="Task title"
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Optional description"
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label>Due Date</label>
                <input
                  type="date"
                  value={form.due_date}
                  onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                  onClick={(e) => e.target.showPicker?.()}
                />
              </div>
              <div className="form-group">
                <label>Priority</label>
                <select
                  value={form.priority}
                  onChange={(e) => setForm({ ...form, priority: e.target.value })}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div className="form-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn">
                  Create Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
