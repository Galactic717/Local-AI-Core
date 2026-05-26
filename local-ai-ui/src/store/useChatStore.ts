import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  type: 'text' | 'image' | 'tool';
  timestamp: number;
  model?: string;
  image_b64?: string;
  toolName?: string;
  toolStatus?: 'ok' | 'error';
}

export interface Session {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
}

interface VramStatus {
  used: number;
  total: number;
  free: number;
  active_model: string | null;
}

interface ChatState {
  sessions: Session[];
  currentSessionId: string;
  vram: VramStatus;
  isProcessing: boolean;
  addMessage: (msg: Omit<Message, 'id' | 'timestamp'>) => void;
  setVram: (vram: VramStatus) => void;
  setProcessing: (status: boolean) => void;
  createNewSession: () => void;
  switchSession: (id: string) => void;
  deleteSession: (id: string) => void;
  clearCurrentSession: () => void;
}

const DEFAULT_SESSION_ID = 'default-neural-core';

const defaultAssistantMessage = (): Message => ({
  id: '1',
  role: 'assistant',
  content: 'Neural Core Online. I can chat, inspect files, run commands, search the web, and generate images. What should we do?',
  type: 'text',
  timestamp: Date.now(),
  model: 'local-core',
});

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      sessions: [
        {
          id: DEFAULT_SESSION_ID,
          title: 'Neural Session #INIT',
          messages: [defaultAssistantMessage()],
          updatedAt: Date.now(),
        },
      ],
      currentSessionId: DEFAULT_SESSION_ID,
      vram: { used: 0, total: 6144, free: 6144, active_model: null },
      isProcessing: false,

      addMessage: (msg) => {
        const { currentSessionId, sessions } = get();
        const newMessage: Message = {
          ...msg,
          id: Math.random().toString(36).slice(2),
          timestamp: Date.now(),
        };

        const updatedSessions = sessions.map((session) => {
          if (session.id !== currentSessionId) {
            return session;
          }

          let newTitle = session.title;
          if (session.messages.length === 1 && msg.role === 'user') {
            newTitle = msg.content.slice(0, 30) + (msg.content.length > 30 ? '...' : '');
          }

          return {
            ...session,
            title: newTitle,
            messages: [...session.messages, newMessage],
            updatedAt: Date.now(),
          };
        });

        set({ sessions: updatedSessions });
      },

      setVram: (vram) => set({ vram }),
      setProcessing: (status) => set({ isProcessing: status }),

      createNewSession: () => {
        const newSession: Session = {
          id: Math.random().toString(36).slice(2),
          title: `Neural Session #${Math.floor(Math.random() * 1000)}`,
          messages: [
            {
              ...defaultAssistantMessage(),
              content: 'New session initialized. I am ready to inspect files, edit code, run commands, and help with local tasks.',
            },
          ],
          updatedAt: Date.now(),
        };

        set((state) => ({
          sessions: [newSession, ...state.sessions],
          currentSessionId: newSession.id,
        }));
      },

      switchSession: (id) => set({ currentSessionId: id }),

      deleteSession: (id) => {
        const { sessions, currentSessionId } = get();
        if (sessions.length === 1) return;

        const newSessions = sessions.filter((session) => session.id !== id);
        set({
          sessions: newSessions,
          currentSessionId: currentSessionId === id ? newSessions[0].id : currentSessionId,
        });
      },

      clearCurrentSession: () => {
        const { currentSessionId, sessions } = get();
        set({
          sessions: sessions.map((session) =>
            session.id === currentSessionId ? { ...session, messages: [], updatedAt: Date.now() } : session
          ),
        });
      },
    }),
    {
      name: 'codex-chat-storage',
      partialize: (state) => ({ sessions: state.sessions, currentSessionId: state.currentSessionId }),
    }
  )
);
