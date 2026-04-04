import React, { useState, useEffect } from 'react';
import { 
  fetchContinuityStatus, 
  fetchOperatorVisibility, 
  fetchOperatorSummary,
  fetchConversations,
  ContinuityStatus,
  OperatorVisibility,
  OperatorSummary,
  Conversation
} from './api';

// ─────────────────────────────────────────────────────────────────────────────
// Layout Components (App Shell v1)
// ─────────────────────────────────────────────────────────────────────────────

const LEFT_WIDTH = 260;
const RIGHT_WIDTH = 320;

function Sidebar({ conversations }: { conversations: Conversation[] }) {
  return (
    <aside
      style={{
        width: LEFT_WIDTH,
        borderRight: '1px solid #e0e0e0',
        padding: '1rem',
        backgroundColor: '#f9f9f9',
        overflowY: 'auto',
      }}
    >
      <nav>
        <h3>Navigation</h3>
        <ul style={{ listStyle: 'none', marginTop: '0.5rem' }}>
          <li style={{ marginBottom: '0.25rem' }}>
            <button style={{ width: '100%', textAlign: 'left' }}>
              💬 Conversations
            </button>
            <div style={{ fontSize: '0.75rem', color: '#666', marginLeft: '0.5rem', marginTop: '0.25rem' }}>
              {conversations.length === 0 
                ? 'No conversations yet' 
                : `${conversations.length} conversation${conversations.length !== 1 ? 's' : ''}`}
            </div>
          </li>
          <li style={{ marginBottom: '0.25rem' }}>
            <button style={{ width: '100%', textAlign: 'left' }}>
              📁 Projects
            </button>
          </li>
          <li style={{ marginBottom: '0.25rem' }}>
            <button style={{ width: '100%', textAlign: 'left' }}>
              📄 Files
            </button>
          </li>
          <li>
            <button style={{ width: '100%', textAlign: 'left' }}>
              ⏳ Continuity Snapshots
            </button>
          </li>
        </ul>
      </nav>
    </aside>
  );
}

function ChatSurface({ continuity }: { continuity: ContinuityStatus }) {
  const [message, setMessage] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  return (
    <main
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid #e0e0e0',
        backgroundColor: '#ffffff',
      }}
    >
      {/* Message Stream */}
      <section
        style={{
          flex: 1,
          padding: '1rem',
          overflowY: 'auto',
          borderBottom: '1px solid #e0e0e0',
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
            maxWidth: '800px',
            margin: '0 auto',
          }}
        >
          <div style={{ padding: '0.5rem 1rem', backgroundColor: '#f0f7ff' }}>
            <strong>🤖 Weslr:</strong> Hello! I'm ready to help. Drop a file or
            start a conversation.
          </div>
          <div
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#f5f5f5',
              alignSelf: 'flex-end',
            }}
          >
            <strong>You:</strong> Can you analyze a JSON file for me?
          </div>
        </div>
      </section>

      {/* File Drop Zone Placeholder */}
      <section
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          console.log('File dropped:', e.dataTransfer.files);
        }}
        style={{
          padding: '0.75rem 1rem',
          backgroundColor: isDragging ? '#e8f4ff' : '#fafafa',
          borderTop: '1px solid #e0e0e0',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}
      >
        <input
          type="file"
          style={{ display: 'none' }}
          id="fileInput"
          multiple
        />
        <button
          onClick={() => document.getElementById('fileInput')?.click()}
          style={{
            padding: '0.5rem 1rem',
            border: '1px solid #007aff',
            backgroundColor: '#007aff',
            color: '#ffffff',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          📎 Attach
        </button>
        <span
          style={{
            flex: 1,
            fontSize: '0.875rem',
            color: '#666',
            textAlign: 'center',
          }}
        >
          Drag & drop files here, or click to browse
        </span>
        <span
          style={{
            fontSize: '0.75rem',
            color: '#00aa00',
            backgroundColor: '#e6ffe6',
            padding: '0.125rem 0.5rem',
            borderRadius: '1rem',
          }}
        >
          STRUCTURED-DATA ROUTING ACTIVE
        </span>
      </section>

      {/* Input Box */}
      <section
        style={{
          padding: '0.75rem 1rem',
          display: 'flex',
          alignItems: 'flex-end',
          gap: '0.5rem',
          backgroundColor: '#fafafa',
          borderTop: '1px solid #e0e0e0',
        }}
      >
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type a message… (Shift+Enter for new line)"
          style={{
            flex: 1,
            padding: '0.5rem 0.75rem',
            border: '1px solid #e0e0e0',
            borderRadius: '4px',
            resize: 'none',
            minHeight: '40px',
            maxHeight: '120px',
            fontFamily: 'inherit',
            fontSize: '0.9375rem',
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              console.log('Send:', message);
              setMessage('');
            }
          }}
        />
        <button
          style={{
            padding: '0.5rem 1rem',
            border: 'none',
            backgroundColor: '#007aff',
            color: '#ffffff',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: '600',
          }}
          onClick={() => {
            console.log('Send:', message);
            setMessage('');
          }}
        >
          Send
        </button>
      </section>

      {/* Continuity Status Indicator */}
      <section
        style={{
          padding: '0.25rem 1rem',
          fontSize: '0.75rem',
          backgroundColor: continuity.active ? '#e6ffe6' : '#ffe6e6',
          borderTop: '1px solid #e0e0e0',
          display: 'flex',
          justifyContent: 'space-between',
        }}
      >
        <span>
          ⏳ Continuity: {continuity.active ? 'active' : 'inactive'}
          {continuity.last_updated && (
            <span style={{ marginLeft: '0.5rem', color: '#666' }}>
              (last: {continuity.last_updated.slice(0, 19).replace('T', ' ')})
            </span>
          )}
        </span>
        <span>📄 Structured data routing: enabled</span>
      </section>
    </main>
  );
}

function OperatorPanel({ 
  visibility, 
  summary 
}: { 
  visibility: OperatorVisibility; 
  summary: OperatorSummary; 
}) {
  const [visible, setVisible] = useState(visibility.visible);

  // Update visibility when backend returns new value
  useEffect(() => {
    setVisible(visibility.visible);
  }, [visibility.visible]);

  return (
    <aside
      style={{
        width: visible ? RIGHT_WIDTH : 0,
        borderLeft: visible ? '1px solid #e0e0e0' : 'none',
        backgroundColor: visible ? '#fafafa' : 'transparent',
        overflow: 'hidden',
        transition: 'width 0.2s ease, border 0.2s ease',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <header
        style={{
          padding: '0.5rem 1rem',
          borderBottom: '1px solid #e0e0e0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <strong>Operator Panel</strong>
        <button
          onClick={() => setVisible((v) => !v)}
          style={{
            padding: '0.25rem 0.5rem',
            border: '1px solid #ccc',
            backgroundColor: 'transparent',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.75rem',
          }}
        >
          {visible ? 'Hide' : 'Show'}
        </button>
      </header>

      {visible && (
        <div
          style={{
            flex: 1,
            padding: '1rem',
            overflowY: 'auto',
            fontSize: '0.875rem',
          }}
        >
          <section style={{ marginBottom: '1rem' }}>
            <h4 style={{ marginBottom: '0.5rem' }}>Proposal Summary</h4>
            <div
              style={{
                padding: '0.75rem',
                border: '1px solid #e0e0e0',
                borderRadius: '4px',
                backgroundColor: '#fff',
              }}
            >
              {summary.total_proposals > 0 ? (
                <>
                  <p style={{ color: '#333' }}>
                    {summary.total_proposals} total proposal{summary.total_proposals !== 1 ? 's' : ''}
                  </p>
                  <p style={{ color: '#666', fontSize: '0.75rem' }}>
                    {summary.pending_reviews} pending review{summary.pending_reviews !== 1 ? 's' : ''}
                  </p>
                  <p style={{ color: '#666', fontSize: '0.75rem' }}>
                    {summary.active_proposals.length} active
                  </p>
                </>
              ) : (
                <>
                  <p style={{ color: '#333' }}>No active proposals.</p>
                  <p style={{ color: '#666', fontSize: '0.75rem', marginTop: '0.5rem' }}>
                    The operator pipeline is listening. When proposals arrive, they
                    will appear here.
                  </p>
                </>
              )}
            </div>
          </section>

          <section>
            <h4 style={{ marginBottom: '0.5rem' }}>Review State</h4>
            <div
              style={{
                padding: '0.75rem',
                border: '1px solid #e0e0e0',
                borderRadius: '4px',
                backgroundColor: '#fff',
              }}
            >
              <p style={{ color: '#333' }}>
                {summary.pending_reviews > 0 
                  ? `${summary.pending_reviews} item${summary.pending_reviews !== 1 ? 's' : ''} ready for review` 
                  : 'Ready for review.'}
              </p>
              <p style={{ color: '#666', fontSize: '0.75rem', marginTop: '0.5rem' }}>
                Review state updates when operator proposals are received.
              </p>
            </div>
          </section>
        </div>
      )}
    </aside>
  );
}

export default function App() {
  const [continuity, setContinuity] = useState<ContinuityStatus>({ active: false });
  const [visibility, setVisibility] = useState<OperatorVisibility>({ visible: true, reason: 'dev', can_review: true });
  const [summary, setSummary] = useState<OperatorSummary>({ active_proposals: [], pending_reviews: 0, total_proposals: 0 });
  const [conversations, setConversations] = useState<Conversation[]>([]);

  // Fetch data from backend contract
  useEffect(() => {
    const fetchData = async () => {
      const [c, v, s, convs] = await Promise.all([
        fetchContinuityStatus(),
        fetchOperatorVisibility(),
        fetchOperatorSummary(),
        fetchConversations(20),
      ]);
      setContinuity(c);
      setVisibility(v);
      setSummary(s);
      setConversations(convs);
    };
    fetchData();
  }, []);

  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'row',
      }}
    >
      <Sidebar conversations={conversations} />
      <ChatSurface continuity={continuity} />
      <OperatorPanel visibility={visibility} summary={summary} />
    </div>
  );
}
