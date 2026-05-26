import React, { useEffect } from 'react';
import { Activity, Cpu } from 'lucide-react';

import { pollHardwareStatus } from '../api/client';
import { useChatStore } from '../store/useChatStore';

export const HardwareMonitor: React.FC = () => {
  const vram = useChatStore((state) => state.vram);

  useEffect(() => {
    pollHardwareStatus();
    const interval = setInterval(pollHardwareStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const usagePercent = vram.total > 0 ? Math.round((vram.used / vram.total) * 100) : 0;
  const isOnline = vram.active_model !== 'Offline';

  return (
    <div className="relative z-10 flex items-center justify-between border-b border-white/5 bg-codex-sidebar/80 px-6 py-2 shadow-2xl backdrop-blur-xl">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="rounded bg-codex-accent/10 p-1">
            <Cpu size={14} className="text-codex-accent" />
          </div>
          <div className="flex flex-col">
            <span className="mb-1 text-[10px] font-bold uppercase leading-none tracking-tighter text-codex-text/40">
              GPU VRAM
            </span>
            <div className="flex items-center gap-2">
              <div className="h-1 w-24 overflow-hidden rounded-full bg-codex-border">
                <div
                  className={`h-full transition-all duration-1000 ${vram.used > 5000 ? 'bg-red-500' : 'bg-codex-accent'}`}
                  style={{ width: `${isOnline ? usagePercent : 0}%` }}
                />
              </div>
              <span className="text-[11px] font-bold text-codex-text/80">
                {isOnline ? `${vram.used}MB / ${vram.total}MB` : 'OFFLINE'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 border-l border-codex-border pl-6">
          <div className="rounded bg-codex-purple/10 p-1">
            <Activity size={14} className="text-codex-purple" />
          </div>
          <div className="flex flex-col">
            <span className="mb-1 text-[10px] font-bold uppercase leading-none tracking-tighter text-codex-text/40">
              Active Model
            </span>
            <span className="text-[11px] font-bold uppercase tracking-tight text-codex-purple">
              {vram.active_model || 'System Idle'}
            </span>
          </div>
        </div>
      </div>

      <div
        className={`flex items-center gap-2 rounded-full border px-3 py-1 ${
          isOnline ? 'border-green-500/20 bg-green-500/5' : 'border-red-500/20 bg-red-500/5'
        }`}
      >
        <div className={`h-1.5 w-1.5 rounded-full ${isOnline ? 'animate-pulse bg-green-500' : 'bg-red-500'}`} />
        <span className={`text-[10px] font-bold ${isOnline ? 'text-green-500/80' : 'text-red-500/80'}`}>
          {isOnline ? 'CORE V1.5' : 'CORE OFFLINE'}
        </span>
      </div>
    </div>
  );
};
