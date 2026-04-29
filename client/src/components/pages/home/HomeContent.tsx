'use client';

import { useState, type FormEvent, type KeyboardEvent } from 'react';
import { useRouter } from 'next/navigation';
import useSWR from 'swr';
import AuthButton from '@/components/shared/AuthButton';
import LoadingScreen from '@/components/shared/LoadingScreen';
import Logo from '@/components/shared/Logo';
import { useAuth } from '@/hooks/useAuth';
import { chatSessions } from '@/lib/api';

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((r) => r.json());

function HomeChatInput({ onSubmit }: { onSubmit: (q: string) => Promise<void> }) {
  const [value, setValue] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    const q = value.trim();
    if (!q || loading) return;
    setLoading(true);
    try {
      await onSubmit(q);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    submit();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex gap-2 items-end rounded-2xl border border-accent/30 bg-surface shadow-sm p-2">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          placeholder="What would you like to cook today?"
          rows={1}
          className="flex-1 resize-none bg-transparent px-3 py-2 text-base text-text placeholder:text-text/40 focus:outline-none disabled:opacity-50 max-h-32 overflow-y-auto"
          style={{ minHeight: '44px' }}
        />
        <button
          type="submit"
          disabled={!value.trim() || loading}
          className="w-11 h-11 rounded-xl flex items-center justify-center bg-primary text-white hover:bg-primary/90 disabled:opacity-40 transition-colors flex-shrink-0"
          aria-label="Start cooking"
        >
          {loading ? (
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
          )}
        </button>
      </div>
    </form>
  );
}

function SuggestionChips({ onSelect }: { onSelect: (q: string) => Promise<void> }) {
  const { data, isLoading } = useSWR<{ suggestions: string[] }>(
    '/api/chat-sessions/home-suggestions',
    fetcher,
    { revalidateOnFocus: false },
  );

  if (isLoading) {
    return (
      <div className="flex flex-wrap gap-2 justify-center">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-8 w-36 rounded-full bg-accent/20 animate-pulse" />
        ))}
      </div>
    );
  }

  const suggestions = data?.suggestions ?? [];
  if (!suggestions.length) return null;

  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {suggestions.map((s) => (
        <button
          key={s}
          onClick={() => onSelect(s)}
          className="px-4 py-1.5 rounded-full border border-accent/30 bg-surface text-sm text-text/80 hover:bg-accent/20 hover:text-text transition-colors"
        >
          {s}
        </button>
      ))}
    </div>
  );
}

export default function HomeContent() {
  const { user, loading } = useAuth();
  const router = useRouter();

  if (loading) {
    return <LoadingScreen />;
  }

  const handleStartChat = async (q: string) => {
    const resp = await chatSessions.create('chat');
    if (resp.error || !resp.data?.session?.id) return;
    const id = resp.data.session.id;
    router.push(`/chat/${id}?q=${encodeURIComponent(q)}`);
  };

  return (
    <div className="flex flex-col flex-1 max-w-2xl mx-auto w-full px-4 py-8">
      {/* Logo + hero */}
      <div className="flex flex-col items-center text-center mt-8 mb-10">
        <div className="mb-6">
          <Logo size="lg" showLink={false} />
        </div>
        <h1 className="text-4xl md:text-5xl font-heading font-bold text-text mb-3">
          Let&apos;s cook something delicious
        </h1>
        <p className="text-lg text-text/60">
          Tell me what you&apos;d like to make and I&apos;ll guide you through it
        </p>
      </div>

      {/* Chat input + suggestions (authenticated only) */}
      {user ? (
        <div className="flex flex-col gap-5">
          <HomeChatInput onSubmit={handleStartChat} />
          <SuggestionChips onSelect={handleStartChat} />
        </div>
      ) : (
        <div className="flex justify-center">
          <AuthButton />
        </div>
      )}
    </div>
  );
}
