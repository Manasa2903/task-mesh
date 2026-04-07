import { useState, useRef, useEffect } from "react";
import { clearChatHistory, fetchChatHistory, sendMessage } from "../api";

const SESSION_STORAGE_KEY = "taskmesh.chat.sessionId";

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [sessionId, setSessionId] = useState(() =>
    localStorage.getItem(SESSION_STORAGE_KEY),
  );
  const messagesEnd = useRef(null);

  useEffect(() => {
    async function loadHistory() {
      if (!sessionId) {
        setHistoryLoading(false);
        return;
      }
      try {
        const history = await fetchChatHistory(sessionId);
        setMessages(
          history.map((msg) => ({
            role: msg.role,
            text: msg.text,
            steps: msg.steps || [],
          })),
        );
      } catch (err) {
        setMessages([
          {
            role: "assistant",
            text: `Could not load chat history: ${err.message}`,
            steps: [],
          },
        ]);
      } finally {
        setHistoryLoading(false);
      }
    }
    loadHistory();
  }, []);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);

    try {
      const data = await sendMessage(text, sessionId);
      setSessionId(data.session_id);
      localStorage.setItem(SESSION_STORAGE_KEY, data.session_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.response, steps: data.steps },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Error: ${err.message}`, steps: [] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    if (loading || historyLoading) return;
    try {
      if (sessionId) {
        await clearChatHistory(sessionId);
      }
    } catch (err) {
      setMessages([
        {
          role: "assistant",
          text: `Could not clear chat history: ${err.message}`,
          steps: [],
        },
      ]);
      return;
    }
    localStorage.removeItem(SESSION_STORAGE_KEY);
    setSessionId(null);
    setMessages([]);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-toolbar">
        <div>
          <h2>Chat</h2>
          <span>{sessionId ? "History saved" : "New chat"}</span>
        </div>
        <button onClick={handleClear} disabled={loading || historyLoading}>
          Clear chat
        </button>
      </div>
      <div className="messages">
        {historyLoading && (
          <div className="message assistant">Loading chat history...</div>
        )}

        {!historyLoading && messages.length === 0 && (
          <div className="empty-state">
            <h3>Welcome to TaskMesh</h3>
            <p>Ask me to manage tasks, schedule meetings, or take notes.</p>
            <p style={{ marginTop: 12, fontSize: 13, color: "var(--text-muted)" }}>
              Try: "Create a task to review the Q4 report by Friday"
              <br />
              or: "Schedule a meeting tomorrow at 3pm and remind me to prepare slides"
              <br />
              or: "Plan my day"
            </p>
          </div>
        )}

        {!historyLoading &&
          messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              {msg.text}
              {msg.steps && msg.steps.length > 0 && (
                <div className="steps-trace">
                  <strong>Execution trace:</strong>
                  {msg.steps.map((step, j) => (
                    <div key={j} className="step">
                      <span className="agent-badge">{step.agent}</span>
                      <span>
                        → {step.tool}({Object.keys(step.args).join(", ")})
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

        {loading && (
          <div className="message assistant">
            <div className="loading">
              <div className="spinner" />
              Agents working...
            </div>
          </div>
        )}
        <div ref={messagesEnd} />
      </div>

      <div className="chat-input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask TaskMesh anything..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
