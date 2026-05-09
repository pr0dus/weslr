import React, { useEffect, useState } from 'react';
import config from './config';
import {
  fetchContinuityStatus,
  fetchOperatorVisibility,
  fetchOperatorSummary,
  fetchConversations,
  uploadFile as uploadFileToBackend,
  sendChatMessage,
  ContinuityStatus,
  OperatorVisibility,
  OperatorSummary,
  Conversation,
} from './api';

const LEFT_WIDTH = 260;
const RIGHT_WIDTH = 320;

interface UiChatMessage {
  id: string;
  sender: 'weslr' | 'you' | 'system';
  text: string;
  timestamp: string;
  result?: any;
}

const examplePrompts = [
  'What is WESLR?',
  'How does governed memory work?',
  'What is the difference between hosted and private WESLR?',
  'What can the public demo do?',
];

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
        <h3>WESLR</h3>
        <p style={{ color: '#666', fontSize: '0.82rem', lineHeight: 1.45 }}>
          Continuity-first reasoning workspace.
        </p>
        <ul style={{ listStyle: 'none', marginTop: '1rem', padding: 0 }}>
          <li style={{ marginBottom: '0.5rem' }}>
            <button style={{ width: '100%', textAlign: 'left' }}>💬 Conversations</button>
            <div style={{ fontSize: '0.75rem', color: '#666', marginLeft: '0.5rem', marginTop: '0.25rem' }}>
              {conversations.length === 0
                ? 'No conversations yet'
                : `${conversations.length} conversation${conversations.length !== 1 ? 's' : ''}`}
            </div>
          </li>
          <li style={{ marginBottom: '0.5rem' }}><button style={{ width: '100%', textAlign: 'left' }}>📁 Projects</button></li>
          <li style={{ marginBottom: '0.5rem' }}><button style={{ width: '100%', textAlign: 'left' }}>📄 Files</button></li>
          <li><button style={{ width: '100%', textAlign: 'left' }}>⏳ Continuity</button></li>
        </ul>
      </nav>
    </aside>
  );
}

function DemoBanner() {
  if (!config.features.showReadOnlyBanner) return null;

  return (
    <section
      style={{
        padding: '0.85rem 1rem',
        background: 'linear-gradient(90deg, #eef6ff, #f7fbff)',
        borderBottom: '1px solid #d7e8ff',
      }}
    >
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <strong>{config.publicDemo.label}</strong>
          <span style={badgeStyle}>Read-only</span>
          <span style={badgeStyle}>No memory writes</span>
          <span style={badgeStyle}>No file upload</span>
          <span style={badgeStyle}>No operator controls</span>
        </div>
        <p style={{ margin: '0.35rem 0 0 0', color: '#445', fontSize: '0.88rem', lineHeight: 1.45 }}>
          {config.publicDemo.subtitle}
        </p>
      </div>
    </section>
  );
}

function ExamplePrompts({ onSelect }: { onSelect: (prompt: string) => void }) {
  if (!config.features.showExamplePrompts) return null;

  return (
    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
      {examplePrompts.map(prompt => (
        <button
          key={prompt}
          onClick={() => onSelect(prompt)}
          style={{
            padding: '0.35rem 0.65rem',
            border: '1px solid #cfe1ff',
            borderRadius: '999px',
            backgroundColor: '#f7fbff',
            cursor: 'pointer',
            fontSize: '0.8rem',
          }}
        >
          {prompt}
        </button>
      ))}
    </div>
  );
}

function ChatResult({ result }: { result: any }) {
  if (!result) return null;

  return (
    <div
      style={{
        padding: '0.75rem 1rem',
        backgroundColor: '#fff4e5',
        borderRadius: '8px',
        border: '1px solid #ffd591',
        fontSize: '0.875rem',
      }}
    >
      <strong style={{ color: '#8a5200' }}>Read-only demo notice</strong>
      <p style={{ margin: '0.25rem 0 0 0', color: '#666' }}>
        {result.error || 'This action is not available in the read-only public demo.'}
      </p>
    </div>
  );
}

function ChatSurface({
  continuity,
  onFileUploaded,
}: {
  continuity: ContinuityStatus;
  onFileUploaded: (result: any) => void;
}) {
  const [message, setMessage] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [messages, setMessages] = useState<UiChatMessage[]>([
    {
      id: 'welcome-1',
      sender: 'weslr',
      text: 'This is a read-only WESLR demo. You can ask what WESLR is, how governed memory works, or why private deployment matters.',
      timestamp: new Date().toISOString(),
    },
  ]);

  const sendMessage = async (text: string) => {
    const clean = text.trim();
    if (!clean) return;

    setMessage('');
    setMessages(prev => [
      ...prev,
      { id: `user-${Date.now()}`, sender: 'you', text: clean, timestamp: new Date().toISOString() },
    ]);

    try {
      const result = await sendChatMessage(clean);
      setMessages(prev => [
        ...prev,
        {
          id: `weslr-${Date.now()}`,
          sender: 'weslr',
          text:
            result.success && result.reply
              ? result.reply
              : result.error || 'This public demo only supports selected read-only WESLR routes.',
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (_e) {
      setMessages(prev => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          sender: 'weslr',
          text: 'Something went wrong while processing this request. No action was executed.',
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  };

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const result = await uploadFileToBackend(file.name, '');
      onFileUploaded(result.result || result);
      setMessages(prev => [
        ...prev,
        {
          id: `file-disabled-${Date.now()}`,
          sender: 'system',
          text: 'File upload disabled',
          timestamp: new Date().toISOString(),
          result: result.result || { error: result.error, category: 'error' },
        },
      ]);
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
        minWidth: 0,
      }}
    >
      <DemoBanner />

      <section style={{ flex: 1, padding: '1rem', overflowY: 'auto', borderBottom: '1px solid #e0e0e0' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '850px', margin: '0 auto' }}>
          <ExamplePrompts onSelect={sendMessage} />
          {messages.map(msg => (
            msg.result ? (
              <ChatResult key={msg.id} result={msg.result} />
            ) : (
              <div
                key={msg.id}
                style={{
                  padding: '0.65rem 1rem',
                  backgroundColor: msg.sender === 'you' ? '#f5f5f5' : '#f0f7ff',
                  alignSelf: msg.sender === 'you' ? 'flex-end' : 'flex-start',
                  borderRadius: msg.sender === 'you' ? '12px 12px 0 12px' : '12px 12px 12px 0',
                  maxWidth: '85%',
                }}
              >
                {msg.sender === 'weslr' && <strong>WESLR:</strong>}
                <p style={{ margin: msg.sender === 'weslr' ? '0.25rem 0 0 0' : 0, lineHeight: 1.45 }}>{msg.text}</p>
              </div>
            )
          ))}
        </div>
      </section>

      {config.features.fileUpload ? (
        <section style={{ padding: '0.75rem 1rem', backgroundColor: '#fafafa', borderTop: '1px solid #e0e0e0' }}>
          <input
            type="file"
            id="fileInput"
            disabled={isUploading}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFileUpload(file);
            }}
          />
        </section>
      ) : (
        <section style={{ padding: '0.55rem 1rem', backgroundColor: '#fffaf2', borderTop: '1px solid #f2dfbf', fontSize: '0.82rem', color: '#755118' }}>
          File upload is disabled in this read-only public demo. Private workspaces and institutional deployments can enable controlled file handling later.
        </section>
      )}

      <section style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'flex-end', gap: '0.5rem', backgroundColor: '#fafafa', borderTop: '1px solid #e0e0e0' }}>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask about WESLR, hosted/private deployment, governed memory, or the public demo…"
          style={{ flex: 1, padding: '0.65rem 0.8rem', border: '1px solid #d8d8d8', borderRadius: '8px', resize: 'none', minHeight: '42px', maxHeight: '120px', fontFamily: 'inherit', fontSize: '0.9375rem' }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendMessage(message);
            }
          }}
        />
        <button
          style={{ padding: '0.65rem 1rem', border: 'none', backgroundColor: '#007aff', color: '#ffffff', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
          onClick={() => sendMessage(message)}
        >
          Send
        </button>
      </section>

      <section style={{ padding: '0.35rem 1rem', fontSize: '0.75rem', backgroundColor: '#f8fbff', borderTop: '1px solid #e0e0e0', display: 'flex', justifyContent: 'space-between', gap: '0.5rem', flexWrap: 'wrap' }}>
        <span>Continuity: {continuity.active ? 'demo context active' : 'inactive'}</span>
        <span>No memory writes · No execution · No operator controls · No file upload</span>
      </section>

      {config.features.showLimitationsFooter && (
        <section style={{ padding: '0.45rem 1rem', fontSize: '0.75rem', color: '#666', backgroundColor: '#fbfbfb', borderTop: '1px solid #eee' }}>
          This public demo is limited. Real memory, private deployment, team workflows, file handling, and operator features require onboarding or a private deployment agreement.
        </section>
      )}
    </main>
  );
}

function OperatorPanel({ visibility, summary }: { visibility: OperatorVisibility; summary: OperatorSummary }) {
  if (!config.features.operatorPanel || !visibility.visible) return null;

  return (
    <aside
      style={{
        width: RIGHT_WIDTH,
        borderLeft: '1px solid #e0e0e0',
        backgroundColor: '#fafafa',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <header style={{ padding: '0.5rem 1rem', borderBottom: '1px solid #e0e0e0' }}>
        <strong>Operator Panel</strong>
      </header>
      <div style={{ flex: 1, padding: '1rem', overflowY: 'auto', fontSize: '0.875rem' }}>
        <section style={{ marginBottom: '1rem' }}>
          <h4 style={{ marginBottom: '0.5rem' }}>Proposal Summary</h4>
          <div style={{ padding: '0.75rem', border: '1px solid #e0e0e0', borderRadius: '4px', backgroundColor: '#fff' }}>
            <p style={{ color: '#333' }}>{summary.total_proposals} total proposals</p>
            <p style={{ color: '#666', fontSize: '0.75rem' }}>{summary.pending_reviews} pending reviews</p>
          </div>
        </section>
      </div>
    </aside>
  );
}

const badgeStyle: React.CSSProperties = {
  fontSize: '0.72rem',
  padding: '0.16rem 0.5rem',
  backgroundColor: '#ffffff',
  border: '1px solid #cfe1ff',
  borderRadius: '999px',
  color: '#24527a',
};

export default function App() {
  const [continuity, setContinuity] = useState<ContinuityStatus>({ active: false, snapshots: [] });
  const [visibility, setVisibility] = useState<OperatorVisibility>({ visible: false, reason: 'public_demo', can_review: false });
  const [summary, setSummary] = useState<OperatorSummary>({ active_proposals: [], pending_reviews: 0, total_proposals: 0 });
  const [conversations, setConversations] = useState<Conversation[]>([]);

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
    console.log('File upload result:', result);
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'row' }}>
      <Sidebar conversations={conversations} />
      <ChatSurface continuity={continuity} onFileUploaded={handleFileUploaded} />
      <OperatorPanel visibility={visibility} summary={summary} />
    </div>
  );
}
