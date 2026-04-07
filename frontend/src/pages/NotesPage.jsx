import { useCallback, useEffect, useState } from 'react';
import { createNote, deleteNote, fetchNotes } from '../api';

export default function NotesPage() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ title: '', content: '', tags: '' });

  const loadNotes = useCallback(async () => {
    setLoading(true);
    try {
      setNotes(await fetchNotes());
    } catch (err) {
      console.error('Failed to load notes:', err);
      setNotes([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadNotes(); }, [loadNotes]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.content.trim()) return;
    const tags = form.tags
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean);
    try {
      await createNote({
        title: form.title,
        content: form.content,
        tags,
      });
      setForm({ title: '', content: '', tags: '' });
      setShowModal(false);
      loadNotes();
    } catch (err) {
      console.error('Failed to create note:', err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteNote(id);
      loadNotes();
    } catch (err) {
      console.error('Failed to delete note:', err);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>Notes</h2>
        <button className="btn" onClick={() => setShowModal(true)}>+ New Note</button>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /> Loading notes...</div>
      ) : notes.length === 0 ? (
        <div className="empty-state">
          <h3>No notes yet</h3>
          <p>Create a note or ask the AI assistant to save one for you.</p>
        </div>
      ) : (
        <div className="task-grid">
          {notes.map((note) => (
            <div key={note.id} className="task-card">
              <h3>{note.title}</h3>
              <p className="task-desc">{note.content}</p>
              {note.tags?.length > 0 && (
                <div className="task-meta">
                  {note.tags.map((tag) => (
                    <span key={tag} className="badge low">{tag}</span>
                  ))}
                </div>
              )}
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <button
                  className="btn-secondary"
                  style={{ fontSize: 12, padding: '6px 12px', color: 'var(--danger)' }}
                  onClick={() => handleDelete(note.id)}
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
            <h3>New Note</h3>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Title</label>
                <input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="Note title"
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label>Content</label>
                <textarea
                  value={form.content}
                  onChange={(e) => setForm({ ...form, content: e.target.value })}
                  placeholder="Write the note"
                  rows={5}
                />
              </div>
              <div className="form-group">
                <label>Tags</label>
                <input
                  value={form.tags}
                  onChange={(e) => setForm({ ...form, tags: e.target.value })}
                  placeholder="work, ideas"
                />
              </div>
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn">Create Note</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
