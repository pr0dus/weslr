import React, { useEffect, useState } from 'react';
import config from './config';
import {
  fetchContinuityStatus,
  fetchOperatorVisibility,
  fetchOperatorSummary,
  uploadFile as uploadFileToBackend,
  sendChatMessage,
  ContinuityStatus,
  OperatorVisibility,
  OperatorSummary,
} from './api';

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
  'Are you just another chatbot?',
  'Can WESLR remember me?',
  'Where does company data go?',
  'Can this demo upload files or run tools?',
  'Can Claude or OpenClaw use WESLR?',
  'Can WESLR improve itself automatically?',
  'What does WESLR cost?',
];

const cards = [
  {
    title: 'Hosted trial',
    text: 'Fastest path to try WESLR with a guided hosted workspace.',
    footer: '1-month free trial · €80/month per user after trial',
  },
  {
    title: 'Private deployment',
    text: 'For organizations that need control over data location, runtime, access, updates, and integrations.',
    footer: 'Quote-based for company and institution needs',
  },
  {
    title: 'Compatible agents',
    text: 'WESLR can complement agents and tools with continuity, governed memory, evidence, proposals, and compact task context.',
    footer: 'Agent/API integrations for private and institutional deployments',
  },
];

function DemoBanner() {
  if (!config.features.showReadOnlyBanner) return null;

  return (
    <section style={styles.banner}>
      <div style={styles.bannerInner}>
        <div style={styles.bannerRow}>
          <strong>{config.publicDemo.label}</strong>
          <span style={styles.badge}>Read-only</span>
          <span style={styles.badge}>No memory writes</span>
          <span style={styles.badge}>No file upload</span>
          <span style={styles.badge}>No operator controls</span>
          <span style={styles.badge}>No deployment controls</span>
        </div>
        <p style={styles.bannerText}>{config.publicDemo.subtitle}</p>
      </div>
    </section>
  );
}

function HeroIntro({ onSelect }: { onSelect: (prompt: string) => void }) {
  return (
    <section style={styles.hero}>
      <div style={styles.heroCopy}>
        <span style={styles.kicker}>Continuity-first cognitive AI</span>
        <h1 style={styles.heroTitle}>WESLR helps long-running work stay coherent.</h1>
        <p style={styles.heroText}>
          WESLR preserves project context, governed memory, evidence, proposals, and approval boundaries around people, teams, and compatible agents.
        </p>
        <p style={styles.heroBoundary}>
          This public demo is read-only. It does not upload files, write memory, expose operator controls, or deploy changes.
        </p>
      </div>
      <div style={styles.heroPanel}>
        <strong>Try asking WESLR</strong>
        <div style={styles.promptGrid}>
          {examplePrompts.map(prompt => (
            <button key={prompt} onClick={() => onSelect(prompt)} style={styles.promptButton}>
              {prompt}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

function TrustCards() {
  return (
    <section style={styles.cardsGrid}>
      {cards.map(card => (
        <article key={card.title} style={styles.card}>
          <h3 style={styles.cardTitle}>{card.title}</h3>
          <p style={styles.cardText}>{card.text}</p>
          <p style={styles.cardFooter}>{card.footer}</p>
        </article>
      ))}
    </section>
  );
}

function ChatResult({ result }: { result: any }) {
  if (!result) return null;

  return (
    <div style={styles.noticeBox}>
      <strong>Read-only demo notice</strong>
      <p style={styles.noticeText}>{result.error || 'This action is not available in the read-only public demo.'}</p>
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
      text: 'This is a read-only WESLR demo. Ask what WESLR is, how governed memory works, why it is not just another chatbot, or what private deployment means.',
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
    <main style={styles.main}>
      <DemoBanner />
      <section style={styles.scrollArea}>
        <div style={styles.contentWrap}>
          <HeroIntro onSelect={sendMessage} />
          <TrustCards />
          <section style={styles.chatCard}>
            <div style={styles.chatHeader}>
              <div>
                <span style={styles.kicker}>Public demo chat</span>
                <h2 style={styles.chatTitle}>Ask WESLR safely</h2>
              </div>
              <span style={styles.statusPill}>No actions executed</span>
            </div>
            <div style={styles.messagesArea}>
              {messages.map(msg => (
                msg.result ? (
                  <ChatResult key={msg.id} result={msg.result} />
                ) : (
                  <div
                    key={msg.id}
                    style={msg.sender === 'you' ? styles.userBubble : msg.sender === 'system' ? styles.systemBubble : styles.weslrBubble}
                  >
                    {msg.sender === 'weslr' && <strong>WESLR</strong>}
                    {msg.sender === 'system' && <strong>System</strong>}
                    <p style={styles.bubbleText}>{msg.text}</p>
                  </div>
                )
              ))}
            </div>
          </section>
        </div>
      </section>

      {config.features.fileUpload ? (
        <section style={styles.fileBar}>
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
        <section style={styles.fileDisabledBar}>
          File upload is disabled in this read-only public demo. Private workspaces and institutional deployments can enable controlled file handling later.
        </section>
      )}

      <section style={styles.composer}>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask about WESLR, governed memory, hosted/private deployment, agents, pricing, or demo limits…"
          style={styles.textarea}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendMessage(message);
            }
          }}
        />
        <button style={styles.sendButton} onClick={() => sendMessage(message)}>
          Send
        </button>
      </section>

      <section style={styles.statusBar}>
        <span>Continuity: {continuity.active ? 'demo context active' : 'inactive'}</span>
        <span>No memory writes · No execution · No operator controls · No file upload</span>
      </section>
    </main>
  );
}

function OperatorPanel({ visibility, summary }: { visibility: OperatorVisibility; summary: OperatorSummary }) {
  if (!config.features.operatorPanel || !visibility.visible) return null;

  return (
    <aside style={styles.operatorPanel}>
      <header style={styles.operatorHeader}><strong>Operator Panel</strong></header>
      <div style={styles.operatorBody}>
        <section>
          <h4>Proposal Summary</h4>
          <div style={styles.operatorCard}>
            <p>{summary.total_proposals} total proposals</p>
            <p>{summary.pending_reviews} pending reviews</p>
          </div>
        </section>
      </div>
    </aside>
  );
}

export default function App() {
  const [continuity, setContinuity] = useState<ContinuityStatus>({ active: false, snapshots: [] });
  const [visibility, setVisibility] = useState<OperatorVisibility>({ visible: false, reason: 'public_demo', can_review: false });
  const [summary, setSummary] = useState<OperatorSummary>({ active_proposals: [], pending_reviews: 0, total_proposals: 0 });

  useEffect(() => {
    const fetchData = async () => {
      const [c, v, s] = await Promise.all([
        fetchContinuityStatus(),
        fetchOperatorVisibility(),
        fetchOperatorSummary(),
      ]);
      setContinuity(c);
      setVisibility(v);
      setSummary(s);
    };
    fetchData();
  }, []);

  const handleFileUploaded = (result: any) => {
    console.log('File upload result:', result);
  };

  return (
    <div style={styles.appShell}>
      <ChatSurface continuity={continuity} onFileUploaded={handleFileUploaded} />
      <OperatorPanel visibility={visibility} summary={summary} />
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  appShell: { minHeight: '100vh', display: 'flex', flexDirection: 'row', background: '#071018', color: '#e7eef8', fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' },
  main: { flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, background: 'radial-gradient(circle at top left, rgba(59,130,246,0.20), transparent 32rem), linear-gradient(180deg, #071018 0%, #0b111b 100%)' },
  banner: { padding: '0.85rem 1rem', background: 'rgba(11, 18, 28, 0.88)', borderBottom: '1px solid rgba(148, 163, 184, 0.18)', backdropFilter: 'blur(12px)' },
  bannerInner: { maxWidth: 1180, margin: '0 auto' },
  bannerRow: { display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' },
  bannerText: { margin: '0.35rem 0 0 0', color: '#b7c4d6', fontSize: '0.88rem', lineHeight: 1.45 },
  badge: { fontSize: '0.72rem', padding: '0.16rem 0.5rem', backgroundColor: 'rgba(96, 165, 250, 0.10)', border: '1px solid rgba(96, 165, 250, 0.35)', borderRadius: '999px', color: '#bfdbfe' },
  scrollArea: { flex: 1, padding: '1.25rem', overflowY: 'auto', borderBottom: '1px solid rgba(148, 163, 184, 0.16)' },
  contentWrap: { display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: 1180, margin: '0 auto' },
  hero: { display: 'grid', gridTemplateColumns: 'minmax(0, 1.25fr) minmax(320px, 0.75fr)', gap: '1rem', alignItems: 'stretch' },
  heroCopy: { padding: '2rem', borderRadius: '24px', background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.94), rgba(30, 41, 59, 0.76))', border: '1px solid rgba(148, 163, 184, 0.22)', boxShadow: '0 24px 80px rgba(0,0,0,0.28)' },
  kicker: { color: '#67e8f9', fontSize: '0.76rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' },
  heroTitle: { margin: '0.65rem 0 0.85rem', fontSize: 'clamp(2rem, 4vw, 4.25rem)', lineHeight: 0.96, letterSpacing: '-0.055em' },
  heroText: { color: '#cbd5e1', fontSize: '1.08rem', lineHeight: 1.6, maxWidth: 760 },
  heroBoundary: { marginTop: '1.25rem', color: '#bae6fd', fontSize: '0.95rem', lineHeight: 1.55 },
  heroPanel: { padding: '1rem', borderRadius: '24px', background: 'rgba(15, 23, 42, 0.72)', border: '1px solid rgba(148, 163, 184, 0.22)' },
  promptGrid: { marginTop: '0.85rem', display: 'grid', gap: '0.55rem' },
  promptButton: { padding: '0.7rem 0.8rem', textAlign: 'left', color: '#dbeafe', background: 'rgba(30, 41, 59, 0.78)', border: '1px solid rgba(96, 165, 250, 0.22)', borderRadius: '14px', cursor: 'pointer', fontSize: '0.88rem' },
  cardsGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '1rem' },
  card: { padding: '1rem', borderRadius: '20px', background: 'rgba(15, 23, 42, 0.68)', border: '1px solid rgba(148, 163, 184, 0.18)' },
  cardTitle: { margin: 0, fontSize: '1rem' },
  cardText: { color: '#cbd5e1', fontSize: '0.9rem', lineHeight: 1.5 },
  cardFooter: { color: '#93c5fd', fontSize: '0.78rem', lineHeight: 1.4 },
  chatCard: { borderRadius: '24px', background: 'rgba(15, 23, 42, 0.78)', border: '1px solid rgba(148, 163, 184, 0.22)', overflow: 'hidden' },
  chatHeader: { display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center', padding: '1rem', borderBottom: '1px solid rgba(148, 163, 184, 0.16)' },
  chatTitle: { margin: '0.25rem 0 0', fontSize: '1.15rem' },
  statusPill: { color: '#bbf7d0', background: 'rgba(34, 197, 94, 0.12)', border: '1px solid rgba(34, 197, 94, 0.3)', borderRadius: '999px', padding: '0.24rem 0.6rem', fontSize: '0.75rem' },
  messagesArea: { display: 'flex', flexDirection: 'column', gap: '0.85rem', padding: '1rem', maxHeight: '42vh', overflowY: 'auto' },
  weslrBubble: { padding: '0.85rem 1rem', backgroundColor: 'rgba(59, 130, 246, 0.14)', border: '1px solid rgba(96, 165, 250, 0.22)', alignSelf: 'flex-start', borderRadius: '16px 16px 16px 4px', maxWidth: '84%' },
  userBubble: { padding: '0.85rem 1rem', backgroundColor: 'rgba(148, 163, 184, 0.14)', border: '1px solid rgba(148, 163, 184, 0.20)', alignSelf: 'flex-end', borderRadius: '16px 16px 4px 16px', maxWidth: '84%' },
  systemBubble: { padding: '0.85rem 1rem', backgroundColor: 'rgba(245, 158, 11, 0.12)', border: '1px solid rgba(245, 158, 11, 0.28)', alignSelf: 'stretch', borderRadius: '16px' },
  bubbleText: { margin: '0.25rem 0 0', lineHeight: 1.55, color: '#e5edf8' },
  noticeBox: { padding: '0.75rem 1rem', backgroundColor: 'rgba(245, 158, 11, 0.12)', borderRadius: '14px', border: '1px solid rgba(245, 158, 11, 0.28)', fontSize: '0.875rem' },
  noticeText: { margin: '0.25rem 0 0', color: '#fde68a' },
  fileBar: { padding: '0.75rem 1rem', backgroundColor: 'rgba(15, 23, 42, 0.92)', borderTop: '1px solid rgba(148, 163, 184, 0.16)' },
  fileDisabledBar: { padding: '0.65rem 1rem', backgroundColor: 'rgba(245, 158, 11, 0.10)', borderTop: '1px solid rgba(245, 158, 11, 0.24)', fontSize: '0.82rem', color: '#fde68a' },
  composer: { padding: '0.85rem 1rem', display: 'flex', alignItems: 'flex-end', gap: '0.65rem', backgroundColor: 'rgba(7, 16, 24, 0.96)', borderTop: '1px solid rgba(148, 163, 184, 0.18)' },
  textarea: { flex: 1, padding: '0.75rem 0.9rem', color: '#e5edf8', background: 'rgba(15, 23, 42, 0.92)', border: '1px solid rgba(148, 163, 184, 0.28)', borderRadius: '14px', resize: 'none', minHeight: '46px', maxHeight: '120px', fontFamily: 'inherit', fontSize: '0.94rem' },
  sendButton: { padding: '0.78rem 1.1rem', border: 'none', background: 'linear-gradient(135deg, #38bdf8, #60a5fa)', color: '#06111f', borderRadius: '14px', cursor: 'pointer', fontWeight: 800 },
  statusBar: { padding: '0.42rem 1rem', fontSize: '0.75rem', color: '#94a3b8', backgroundColor: 'rgba(7, 16, 24, 0.98)', borderTop: '1px solid rgba(148, 163, 184, 0.16)', display: 'flex', justifyContent: 'space-between', gap: '0.5rem', flexWrap: 'wrap' },
  operatorPanel: { width: RIGHT_WIDTH, borderLeft: '1px solid rgba(148, 163, 184, 0.18)', backgroundColor: '#0f172a', overflow: 'hidden', display: 'flex', flexDirection: 'column' },
  operatorHeader: { padding: '0.5rem 1rem', borderBottom: '1px solid rgba(148, 163, 184, 0.18)' },
  operatorBody: { flex: 1, padding: '1rem', overflowY: 'auto', fontSize: '0.875rem' },
  operatorCard: { padding: '0.75rem', border: '1px solid rgba(148, 163, 184, 0.18)', borderRadius: '12px', backgroundColor: 'rgba(15, 23, 42, 0.92)' },
};
