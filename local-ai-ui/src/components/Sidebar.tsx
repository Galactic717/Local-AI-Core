import React from 'react';
import { useChatStore } from '../store/useChatStore';
import { Terminal, Plus, Trash2, BrainCircuit, ShieldCheck, Settings } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const Sidebar: React.FC = () => {
  const { 
    sessions, 
    currentSessionId, 
    switchSession, 
    createNewSession, 
    deleteSession 
  } = useChatStore();

  return (
    <div className="hidden w-72 flex-col border-r border-codex-border bg-codex-sidebar md:flex">
      {/* Header */}
      <div className="mb-4 flex items-center gap-3 p-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-codex-accent text-codex-bg shadow-[0_0_15px_rgba(88,166,255,0.4)]">
          <BrainCircuit size={20} />
        </div>
        <div className="flex flex-col">
          <span className="text-lg font-black leading-none tracking-tighter">CODEX</span>
          <span className="mt-1 text-[9px] font-bold tracking-[0.3em] text-codex-accent">ASSISTANT</span>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="px-4 mb-6">
        <button 
          onClick={createNewSession}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-codex-border p-3 text-[12px] font-bold text-codex-text/60 transition-all hover:border-codex-accent hover:text-codex-accent"
        >
          <Plus size={14} />
          NEW NEURAL SESSION
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 space-y-6 overflow-y-auto px-4 custom-scrollbar">
        <div>
          <div className="mb-3 px-2 text-[10px] font-bold uppercase tracking-[0.2em] text-codex-text/30">
            Sessions History
          </div>
          <div className="space-y-2">
            {sessions.map((session) => (
              <div key={session.id} className="group relative">
                <button
                  onClick={() => switchSession(session.id)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left text-[13px] transition-all",
                    session.id === currentSessionId
                      ? "border-codex-accent/20 bg-codex-accent/5 text-white"
                      : "border-transparent text-codex-text/50 hover:bg-codex-border/20"
                  )}
                >
                  <Terminal size={14} className={cn(session.id === currentSessionId ? "text-codex-accent" : "text-codex-text/30")} />
                  <span className="truncate pr-6 font-medium">{session.title}</span>
                </button>
                {sessions.length > 1 && (
                  <button 
                    onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 text-codex-text/30 hover:text-red-500 transition-all"
                  >
                    <Trash2 size={12} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Protocols */}
        <div>
          <div className="mb-3 px-2 text-[10px] font-bold uppercase tracking-[0.2em] text-codex-text/30">
            Core Protocols
          </div>
          <div className="space-y-1">
            {[
              { name: 'Vision Interface', active: true },
              { name: 'Voice Synthesis', active: true },
              { name: 'Neural Router', active: true },
              { name: 'Local VRAM Sync', active: true }
            ].map((p) => (
              <div key={p.name} className="flex items-center gap-3 px-3 py-2 text-[11px] text-codex-text/40">
                <ShieldCheck size={12} className="text-green-500/40" />
                {p.name}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer Settings */}
      <div className="space-y-2 border-t border-codex-border bg-codex-sidebar/80 p-6">
        <button className="flex w-full items-center justify-between px-2 py-2 text-[11px] font-bold text-codex-text/30 transition-colors hover:text-codex-accent">
          <div className="flex items-center gap-3 uppercase tracking-widest">
            <Settings size={14} />
            <span>Settings</span>
          </div>
          <span className="rounded border border-codex-border px-1.5 py-0.5 text-[8px]">CTRL+,</span>
        </button>
      </div>
    </div>
  );
};
