'use client';

import { useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import useSWR from 'swr';
import AuthButton from '@/components/shared/AuthButton';
import LoadingScreen from '@/components/shared/LoadingScreen';
import Logo from '@/components/shared/Logo';
import ChatInput, { type ChatInputHandle } from '@/components/shared/chat/ChatInput';
import { useAuth } from '@/hooks/useAuth';
import { chatSessions } from '@/lib/api';

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((r) => r.json());

function SuggestionChips({ onSelect }: { onSelect: (q: string) => void }) {
  const [t] = useState(() => Date.now() - new Date().getTimezoneOffset() * 60000);
  const { data, isLoading } = useSWR<{ suggestions: string[] }>(
    `/api/chat-sessions/home-suggestions?t=${t}`,
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

  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {suggestions.map((s) => (
        <button
          key={s}
          onClick={() => onSelect(s)}
          className="cursor-pointer px-4 py-1.5 rounded-full border border-accent/30 bg-surface text-sm text-text/80 hover:bg-accent/20 hover:text-text transition-colors"
        >
          {s}
        </button>
      ))}
    </div>
  );
}

export default function HomeContent() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const chatInputRef = useRef<ChatInputHandle>(null);

  if (authLoading) {
    return <LoadingScreen />;
  }

  const handleStartChat = async (q: string) => {
    if (submitting) return;
    setSubmitting(true);
    try {
      const resp = await chatSessions.create('chat', undefined);
      if (resp.error || !resp.data?.session?.id) return;
      const id = resp.data.session.id;
      router.push(`/chat/${id}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col justify-center flex-1 max-w-2xl mx-auto w-full px-4 py-8">
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
          <ChatInput
            ref={chatInputRef}
            onSend={(q) => void handleStartChat(q)}
            loading={submitting}
            placeholder="What would you like to cook today?"
            variant="home"
          />
          <SuggestionChips onSelect={(s) => chatInputRef.current?.setValue(s)} />
        </div>
      ) : (
        <div className="flex justify-center">
          <AuthButton />
        </div>
      )}
    </div>
  );
}
