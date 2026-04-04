import React, { useState, useEffect } from 'react';
import { 
  fetchContinuityStatus, 
  fetchOperatorVisibility, 
  fetchOperatorSummary,
  fetchConversations,
  uploadFile as uploadFileToBackend,
  ContinuityStatus,
  OperatorVisibility,
  OperatorSummary,
  WeslrCandidate,
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

// ─────────────────────────────────────────────────────────────────────────────
// Chat Result Renderer for File Uploads
// ─────────────────────────────────────────────────────────────────────────────

function ChatResult({ result }: { result: any }) {
  if (!result) return null;

  const isError = result.error || result.category === 'error';

  return (
    <div
      style={{
        padding: '0.75rem 1rem',
        backgroundColor: isError ? '#ffe6e6' : '#e6f7ff',
        borderRadius: '8px',
        border: isError ? '1px solid #ff6b6b' : '1px solid #1890ff',
        fontSize: '0.875rem',
      }}
    >
      {isError ? (
        <div>
          <strong style={{ color: '#d93025' }}>⚠️ Upload Error</strong>
          <p style={{ margin: '0.25rem 0 0 0', color: '#666' }}>{result.error || 'Unknown error'}</p>
        </div>
      ) : (
        <>
          <div
            style={{
              marginBottom: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <strong style={{ color: '#1890ff' }}>📄 File Routed:</strong>
            <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', backgroundColor: '#fff', padding: '0.125rem 0.25rem', borderRadius: '4px' }}>
              {result.metadata?.source_file || result.filename || 'unnamed'}
            </span>
          </div>

          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.5rem',
              marginBottom: '0.5rem',
            }}
          >
            {result.category && (
              <span
                style={{
                  fontSize: '0.7rem',
                  padding: '0.125rem 0.5rem',
                  backgroundColor: '#e6f7ff',
                  color: '#1890ff',
                  borderRadius: '1rem',
                }}
              >
                Category: {result.category}
              </span>
            )}
            {result.relevance && (
              <span
                style={{
                  fontSize: '0.7rem',
                  padding: '0.125rem 0.5rem',
                  backgroundColor: '#e6ffe6',
                  color: '#52c41a',
                  borderRadius: '1rem',
                }}
              >
                Relevance: {result.relevance}
              </span>
            )}
            {result.safety?.injection_risk && (
              <span
                style={{
                  fontSize: '0.7rem',
                  padding: '0.125rem 0.5rem',
                  backgroundColor: '#f6ffed',
                  color: '#73d13d',
                  borderRadius: '1rem',
                }}
              >
                Safe: {result.safety.injection_risk} risk
              </span>
            )}
          </div>

          <div
            style={{
              padding: '0.5rem',
              backgroundColor: '#fff',
              borderRadius: '4px',
              fontFamily: 'monospace',
              fontSize: '0.8rem',
              overflowX: 'auto',
            }}
          >
            {result.content || '[No content available]'}
          </div>
        </>
      )}
    </div>
  );
}

function ChatSurface({ 
  continuity, 
  onFileUploaded 
}: { 
  continuity: ContinuityStatus;
  onFileUploaded: (result: any) => void;
}) {
  const [message, setMessage] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome-1',
      sender: 'weslr',
      text: "Hello! I'm ready to help. Drop a file or start a conversation.",
      timestamp: new Date().toISOString(),
    },
  ]);

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const arrayBuffer = await file.arrayBuffer();
      const bytes = new Uint8Array(arrayBuffer);
      
      // Encode as base64 for backend
      const base64Content = btoa(
        Array.from(bytes).map(b => String.fromCharCode(b)).join('')
      );
      
      const result = await uploadFileToBackend(file.name, base64Content);
      
      if (result.success) {
        const fileResult = result.result;
        onFileUploaded(fileResult);
        
        // Add system message with file understanding result
        const newMessage: ChatMessage = {
          id: `file-${Date.now()}`,
          sender: 'system',
          text: `File uploaded: ${file.name}`,
          timestamp: new Date().toISOString(),
          result: fileResult,
        };
        setMessages(prev => [...prev, newMessage]);
      } else {
        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          sender: 'system',
          text: `Upload failed`,
          timestamp: new Date().toISOString(),
          result: { error: result.error, category: 'error' },
        };
        setMessages(prev => [...prev, errorMessage]);
        onFileUploaded({ error: result.error, category: 'error' });
      }
    } catch (e) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        sender: 'system',
        text: `Upload failed`,
        timestamp: new Date().toISOString(),
        result: { error: String(e), category: 'error' },
      };
      setMessages(prev => [...prev, errorMessage]);
      onFileUploaded({ error: String(e), category: 'error' });
    } finally {
      setIsUploading(false);
    }
  };

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
          {messages.map(msg => (
            msg.result ? (
              <ChatResult key={msg.id} result={msg.result} />
            ) : (
              <div
                key={msg.id}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: msg.sender === 'you' ? '#f5f5f5' : '#f0f7ff',
                  alignSelf: msg.sender === 'you' ? 'flex-end' : 'flex-start',
                  borderRadius: msg.sender === 'you' ? '8px 8px 0 8px' : '8px 8px 8px 0',
                }}
              >
                {msg.sender === 'weslr' && <strong>🤖 Weslr:</strong>}
                <p style={{ margin: '0.25rem 0 0 0' }}>{msg.text}</p>
              </div>
            )
          ))}
        </div>
      </section>

      {/* File Drop Zone */}
      <section
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          const file = e.dataTransfer.files[0];
          if (file) {
            handleFileUpload(file);
          }
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
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              handleFileUpload(file);
            }
          }}
        />
        <button
          onClick={() => document.getElementById('fileInput')?.click()}
          disabled={isUploading}
          style={{
            padding: '0.5rem 1rem',
            border: '1px solid #007aff',
            backgroundColor: isUploading ? '#ccc' : '#007aff',
            color: '#ffffff',
            borderRadius: '4px',
            cursor: isUploading ? 'not-allowed' : 'pointer',
            opacity: isUploading ? 0.7 : 1,
          }}
        >
          {isUploading ? '📤 Uploading...' : '📎 Attach'}
        </button>
        <span
          style={{
            flex: 1,
            fontSize: '0.875rem',
            color: '#666',
            textAlign: 'center',
          }}
        >
          {isUploading 
            ? 'Uploading file...' 
            : 'Drag & drop files here, or click to browse'}
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

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string;
  sender: 'weslr' | 'you' | 'system';
  text: string;
  timestamp: string;
  result?: any;
}

function OperatorPanel({ 
  visibility, 
  summary 
}: { 
  visibility: OperatorVisibility; 
  summary: OperatorSummary; 
}) {
  const [visible, setVisible] = useState(visibility.visible);
  const [expandedCandidates, setExpandedCandidates] = useState<Record<string, boolean>>({});

  // Update visibility when backend returns new value
  useEffect(() => {
    setVisible(visibility.visible);
  }, [visibility.visible]);

  // Helper to toggle candidate expansion
  const toggleCandidate = (id: string) => {
    setExpandedCandidates(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  // Helper to mark candidate as reviewed
  const markCandidateReview = async (id: string, action: 'approve' | 'deny' | 'mark-eligible') => {
    const reason = action === 'deny' ? 'Candidate rejected by operator' : '';
    
    try {
      const response = await fetch(`/weslr_backend_contract.py/review-suggestion?candidate_id=${id}&action=${action}&reason=${encodeURIComponent(reason)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          console.log(`Successfully marked ${id} as ${action}`, result);
          // Refresh the operator summary to show updated state
          fetchOperatorSummary();
        } else {
          console.error(`Failed to mark ${id} as ${action}:`, result.error);
        }
      } else {
        console.error(`HTTP error marking ${id} as ${action}:`, response.statusText);
      }
    } catch (error) {
      console.error(`Error marking ${id} as ${action}:`, error);
      // Fallback: just log for now if fetch fails (development mode)
      console.log(`Development mode: Would mark ${id} as ${action}`);
    }
  };

  // Render a single Weslr candidate card
  const renderWeslrCandidate = (c: WeslrCandidate) => {
    const isExpanded = expandedCandidates[c.id] || false;
    
    const priorityColor = {
      high: '#ef4444',
      medium: '#f59e0b',
      low: '#6b7280'
    }[c.weslr_assessment?.priority || 'low'];
    
    const riskColor = {
      high: '#ef4444',
      medium: '#f59e0b',
      low: '#10b981'
    }[c.weslr_assessment?.implementation_risk || 'low'];
    
    return (
      <div
        key={c.id}
        style={{
          padding: '0.75rem',
          marginBottom: '0.5rem',
          border: '1px solid #e0e0e0',
          borderRadius: '4px',
          backgroundColor: '#fff',
          cursor: 'pointer',
        }}
        onClick={() => toggleCandidate(c.id)}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <strong style={{ fontSize: '0.875rem', color: '#333' }}>{c.title || c.id}</strong>
          <span style={{ fontSize: '0.75rem', color: '#666' }}>{c.id}</span>
        </div>
        
        <div style={{ 
          display: 'flex', 
          gap: '0.5rem', 
          marginTop: '0.5rem',
          fontSize: '0.75rem'
        }}>
          <span style={{ 
            padding: '0.125rem 0.5rem',
            borderRadius: '4px',
            backgroundColor: priorityColor,
            color: '#fff',
            fontWeight: 'bold'
          }}>
            {c.weslr_assessment?.priority?.toUpperCase() || 'N/A'}
          </span>
          <span style={{ color: '#10b981', fontWeight: 'bold' }}>
            Fit: {c.weslr_assessment?.fit_score || 'N/A'}
          </span>
          <span style={{ color: riskColor, fontWeight: 'bold' }}>
            Risk: {c.weslr_assessment?.implementation_risk?.toUpperCase() || 'N/A'}
          </span>
        </div>
        
        {isExpanded && c.weslr_assessment && (
          <div style={{ 
            marginTop: '0.5rem',
            paddingTop: '0.5rem',
            borderTop: '1px solid #e0e0e0'
          }}>
            <p style={{ fontSize: '0.75rem', color: '#666', margin: '0.25rem 0' }}>
              <strong>Recommended:</strong> {c.weslr_assessment.recommended_action}
            </p>
            <p style={{ 
              fontSize: '0.7rem', 
              color: '#888', 
              margin: '0.25rem 0',
              lineHeight: '1.4'
            }}>
              {c.weslr_assessment.reasoning}
            </p>
            
            {/* Review Actions */}
            <div style={{ 
              marginTop: '0.5rem', 
              display: 'flex', 
              gap: '0.5rem',
              flexWrap: 'wrap'
            }}>
              <button
                onClick={(e) => { e.stopPropagation(); markCandidateReview(c.id, 'approve'); }}
                style={{
                  padding: '0.25rem 0.75rem',
                  backgroundColor: '#10b981',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '0.7rem',
                  cursor: 'pointer'
                }}
              >
                ✓ Approve
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); markCandidateReview(c.id, 'deny'); }}
                style={{
                  padding: '0.25rem 0.75rem',
                  backgroundColor: '#ef4444',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '0.7rem',
                  cursor: 'pointer'
                }}
              >
                ✕ Deny
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); markCandidateReview(c.id, 'mark-eligible'); }}
                style={{
                  padding: '0.25rem 0.75rem',
                  backgroundColor: '#3b82f6',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '0.7rem',
                  cursor: 'pointer'
                }}
              >
                ✔ Mark Eligible
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

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

          {summary.weslr_candidates && summary.weslr_candidates.length > 0 && (
            <section style={{ marginTop: '1rem' }}>
              <h4 style={{ marginBottom: '0.5rem' }}>Weslr Suggestions</h4>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {summary.weslr_candidates.map(renderWeslrCandidate)}
              </div>
            </section>
          )}
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

  const handleFileUploaded = (result: any) => {
    console.log('File upload complete:', result);
    // In a real app, this would add the result to the chat stream
    // For now, just log it
  };

  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'row',
      }}
    >
      <Sidebar conversations={conversations} />
      <ChatSurface 
        continuity={continuity} 
        onFileUploaded={handleFileUploaded}
      />
      <OperatorPanel visibility={visibility} summary={summary} />
    </div>
  );
}
