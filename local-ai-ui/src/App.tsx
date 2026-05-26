import { Sidebar } from './components/Sidebar';
import { ChatWindow } from './components/ChatWindow';
import { HardwareMonitor } from './components/HardwareMonitor';
import { InputArea } from './components/InputArea';
import { BrainCircuit, Menu } from 'lucide-react';

function App() {
  return (
    <div className="flex h-screen bg-codex-bg font-mono text-codex-text selection:bg-codex-accent/30">
      <Sidebar />

      <div className="relative flex h-full flex-1 flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b border-codex-border/50 px-4 py-3 md:hidden">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-codex-accent text-codex-bg">
              <BrainCircuit size={18} />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-black leading-none tracking-tight">CODEX</span>
              <span className="text-[9px] uppercase tracking-[0.25em] text-codex-accent">Local Core</span>
            </div>
          </div>
          <button className="rounded-lg border border-codex-border p-2 text-codex-text/60">
            <Menu size={16} />
          </button>
        </div>

        <div className="pointer-events-none absolute right-[-10%] top-[-10%] h-[50%] w-[50%] rounded-full bg-codex-accent/5 blur-[120px]" />
        <div className="pointer-events-none absolute bottom-[-10%] left-[-10%] h-[50%] w-[50%] rounded-full bg-codex-purple/5 blur-[120px]" />

        <HardwareMonitor />
        <ChatWindow />
        <InputArea />
      </div>
    </div>
  );
}

export default App;
