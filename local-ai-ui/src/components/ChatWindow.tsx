import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, Command, Sparkles, User, Volume2 } from 'lucide-react';

import { synthesizeSpeech } from '../api/client';
import { useChatStore } from '../store/useChatStore';

export const ChatWindow: React.FC = () => {
  const { sessions, currentSessionId } = useChatStore();
  const currentSession = sessions.find((session) => session.id === currentSessionId);
  const messages = currentSession?.messages || [];
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length]);

  return (
    <div ref={scrollRef} className="codex-grid flex-1 space-y-8 overflow-y-auto p-8 scroll-smooth">
      <div className="mx-auto max-w-4xl space-y-8">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`group flex gap-8 animate-in fade-in slide-in-from-bottom-2 duration-300 ${
              message.role === 'user' ? 'flex-row-reverse' : ''
            }`}
          >
            <div
              className={`glow-blue flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border transition-transform group-hover:scale-110 ${
                message.role === 'assistant'
                  ? 'border-codex-accent/30 bg-codex-accent/10 text-codex-accent'
                  : 'border-codex-border bg-codex-panel text-codex-text/50'
              }`}
            >
              {message.role === 'assistant' ? <Bot size={22} /> : <User size={22} />}
            </div>

            <div className={`flex flex-1 flex-col gap-2 ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div
                className={`relative rounded-2xl border px-5 py-4 text-[14px] leading-relaxed ${
                  message.role === 'user'
                    ? 'border-codex-border bg-codex-panel text-codex-text'
                    : 'border-transparent bg-transparent text-codex-text'
                }`}
              >
                {message.type === 'text' ? (
                  <div className="prose prose-invert prose-blue max-w-none prose-pre:border prose-pre:border-codex-border prose-pre:bg-codex-sidebar">
                    {message.image_b64 && (
                      <img 
                        src={message.image_b64.startsWith('data:') ? message.image_b64 : `data:image/jpeg;base64,${message.image_b64}`} 
                        className="mb-4 max-w-xs rounded-xl border border-codex-border shadow-lg" 
                        alt="Attached by user" 
                      />
                    )}
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                ) : message.type === 'tool' ? (
                  <div className="space-y-3 font-mono text-[12px] text-codex-text/85">
                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-codex-accent/80">
                      <Command size={12} />
                      {message.toolName || 'tool'}
                      <span className={message.toolStatus === 'error' ? 'text-red-400' : 'text-green-400'}>
                        {message.toolStatus || 'ok'}
                      </span>
                    </div>
                    <div className="whitespace-pre-wrap rounded-xl border border-codex-border bg-codex-sidebar/60 px-4 py-3">
                      {message.content}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <img
                      src={`data:image/png;base64,${message.content}`}
                      alt="AI generated output"
                      className="max-w-full cursor-zoom-in rounded-xl border border-codex-border shadow-2xl transition-all hover:scale-[1.02]"
                    />
                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-codex-accent/60">
                      <Sparkles size={12} className="animate-pulse" />
                      Neural Synthesis Complete
                    </div>
                  </div>
                )}

                {message.role === 'assistant' && message.type === 'text' && message.content && (
                  <button
                    onClick={() => synthesizeSpeech(message.content)}
                    className="absolute -right-12 top-0 rounded-lg border border-codex-border bg-codex-bg p-2 text-codex-text/20 opacity-0 shadow-xl transition-all group-hover:opacity-100 hover:text-codex-accent"
                  >
                    <Volume2 size={16} />
                  </button>
                )}
              </div>

              <span className="mx-1 text-[10px] font-bold uppercase tracking-tight text-codex-text/20">
                {message.role}
                {message.model ? ` | ${message.model}` : ''}
                {` | ${new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
