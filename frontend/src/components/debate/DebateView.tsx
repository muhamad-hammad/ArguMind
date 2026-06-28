'use client';

import { useState, useEffect } from 'react';
import LoadingView from './LoadingView';
import DebateStream from './DebateStream';
import SummaryCard from './SummaryCard';
import BrutalButton from '@/components/ui/BrutalButton';
import { DebateResult } from '@/types/debate';

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

interface DebateViewProps {
  topic: string;
  rounds: number;
  onBack: () => void;
  onOpenConfig: () => void;
}

export default function DebateView({ topic, rounds, onBack, onOpenConfig }: DebateViewProps) {
  const [status, setStatus]         = useState<'loading' | 'success' | 'error'>('loading');
  const [transcript, setTranscript] = useState<DebateResult | null>(null);
  const [error, setError]           = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setStatus('loading');
      try {
        const provider = localStorage.getItem('llm_provider') || '';
        const key = localStorage.getItem('llm_key') || '';
        
        const res = await fetch(`${BACKEND}/debate`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'X-LLM-Provider': provider,
            'X-LLM-Key': key
          },
          body: JSON.stringify({ topic, rounds }),
        });
        if (!res.ok) { const t = await res.text(); throw new Error(`Server error (${res.status}): ${t}`); }
        const data: DebateResult = await res.json();
        if (!cancelled) { setTranscript(data); setStatus('success'); }
      } catch (e) {
        if (!cancelled) { setError((e as Error).message); setStatus('error'); }
      }
    })();
    return () => { cancelled = true; };
  }, [topic, rounds]);

  if (status === 'loading') return <LoadingView topic={topic} />;

  if (status === 'error') {
    const isAuthError = /\b401\b|unauthor|api key|api_key|user not found|invalid_api_key|incorrect api key/i.test(error);

    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', padding: 32 }}>
        <div style={{ background: '#06B6D4', border: '4px solid #111', boxShadow: '8px 8px 0 0 #111', padding: 36, maxWidth: 520, textAlign: 'center' }}>
          <div style={{ fontFamily: 'Bangers, cursive', fontSize: 32, marginBottom: 16, color: '#fff' }}>DEBATE FAILED</div>
          <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 16, fontFamily: 'monospace', background: '#fff', border: '2px solid #111', padding: 12, textAlign: 'left' }}>{error}</div>
          {isAuthError ? (
            <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.9)', marginBottom: 24, lineHeight: 1.6 }}>
              Your API key was rejected. Open <strong>CONFIG</strong>, pick the matching provider,
              and paste a valid, active key — then try again.
            </div>
          ) : (
            <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.9)', marginBottom: 24, lineHeight: 1.6 }}>
              Couldn&apos;t reach the backend. If running locally, start it with:<br />
              <code style={{ background: 'rgba(0,0,0,0.2)', padding: '4px 8px', display: 'inline-block', marginTop: 8 }}>
                cd backend &amp;&amp; uvicorn main:app --reload
              </code>
            </div>
          )}
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            {isAuthError && (
              <BrutalButton variant="primary" label="⚙ CONFIG" onClick={onOpenConfig} />
            )}
            <BrutalButton variant="danger" label="TRY AGAIN" onClick={() => setStatus('loading')} style={{ background: '#1E1B4B', color: '#fff' }} />
            <BrutalButton variant="secondary" label="← BACK" onClick={onBack} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ background: '#F5F0E8', minHeight: '100vh' }}>
      <DebateStream messages={transcript!.messages} topic={transcript!.topic} />
      <SummaryCard messages={transcript!.messages} topic={transcript!.topic} judgment={transcript!.judgment} onNewDebate={onBack} />
    </div>
  );
}
