import { useChatStore } from '../store/useChatStore';

const ORCHESTRATOR_URL = import.meta.env.VITE_ORCHESTRATOR_URL ?? 'http://127.0.0.1:8004';
const STT_URL = import.meta.env.VITE_STT_URL ?? 'http://127.0.0.1:8001/v1/audio/transcriptions';
const IMAGE_URL = import.meta.env.VITE_IMAGE_URL ?? 'http://127.0.0.1:8003/api/v1/generate';
const TTS_URL = import.meta.env.VITE_TTS_URL ?? 'http://127.0.0.1:8002/v1/audio/speech';
const BRAIN_ROUTER_URL = import.meta.env.VITE_BRAIN_ROUTER_URL ?? 'http://127.0.0.1:8000/api/v2/agent/chat';

type ToolEvent = {
  type: string;
  tool: string;
  status: 'ok' | 'error';
  summary: string;
};

type RouterResponse = {
  model?: string;
  image_b64?: string;
  events?: ToolEvent[];
  choices?: Array<{
    message?: {
      role?: string;
      content?: string | null;
    };
  }>;
  message?: {
    content?: string | null;
  };
  content?: string | null;
};

const extractReply = (data: RouterResponse) =>
  data.choices?.[0]?.message?.content ?? data.message?.content ?? data.content ?? '';

export const pollHardwareStatus = async () => {
  try {
    const response = await fetch(`${ORCHESTRATOR_URL}/status`);
    if (!response.ok) {
      return;
    }

    const data = await response.json();
    useChatStore.getState().setVram({
      used: data.used_mb || 0,
      total: data.total_mb || 6144,
      free: data.free_mb || 0,
      active_model: data.active_model || 'Idle',
    });
  } catch {
    useChatStore.getState().setVram({
      used: 0,
      total: 6144,
      free: 0,
      active_model: 'Offline',
    });
  }
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const streamChat = async (_prompt: string) => {
  const store = useChatStore.getState();
  const { setProcessing, currentSessionId, sessions } = store;
  const currentSession = sessions.find((session) => session.id === currentSessionId);
  if (!currentSession) return;

  setProcessing(true);

  const history = currentSession.messages
    .filter((message) => message.type === 'text')
    .map((message) => ({
      role: message.role,
      content: message.content,
      ...(message.image_b64 ? { images: [message.image_b64] } : {}),
    }));

  const assistantMsgId = Math.random().toString(36).slice(2);

  useChatStore.setState((state) => ({
    sessions: state.sessions.map((session) =>
      session.id === currentSessionId
        ? {
            ...session,
            messages: [
              ...session.messages,
              {
                id: assistantMsgId,
                role: 'assistant',
                content: 'Working on it...',
                type: 'text',
                timestamp: Date.now(),
              },
            ],
          }
        : session
    ),
  }));

  try {
    const response = await fetch(BRAIN_ROUTER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: history,
        stream: false,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Router error: ${errorText}`);
    }

    const data: RouterResponse = await response.json();
    const reply = extractReply(data) || (data.image_b64 ? 'Here is the generated image.' : 'Empty response.');
    const toolMessages = (data.events ?? []).map((event) => ({
      id: Math.random().toString(36).slice(2),
      role: 'assistant' as const,
      content: event.summary,
      type: 'tool' as const,
      timestamp: Date.now(),
      model: 'tool-runtime',
      toolName: event.tool,
      toolStatus: event.status,
    }));

    const finalMessage = {
      id: assistantMsgId,
      role: 'assistant' as const,
      content: reply,
      type: 'text' as const,
      timestamp: Date.now(),
      model: data.model || 'agent',
    };

    const imageMessage = data.image_b64
      ? {
          id: Math.random().toString(36).slice(2),
          role: 'assistant' as const,
          content: data.image_b64,
          type: 'image' as const,
          timestamp: Date.now(),
          model: data.model || 'sd_turbo',
        }
      : null;

    useChatStore.setState((state) => ({
      sessions: state.sessions.map((session) =>
        session.id === currentSessionId
          ? {
              ...session,
              messages: [
                ...session.messages.filter((message) => message.id !== assistantMsgId),
                ...toolMessages,
                finalMessage,
                ...(imageMessage ? [imageMessage] : []),
              ],
            }
          : session
      ),
    }));

    if (reply && !data.image_b64) {
      await synthesizeSpeech(reply);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    useChatStore.setState((state) => ({
      sessions: state.sessions.map((session) =>
        session.id === currentSessionId
          ? {
              ...session,
              messages: session.messages.map((messageItem) =>
                messageItem.id === assistantMsgId
                  ? {
                      ...messageItem,
                      content: `Agent error: ${message}`,
                      model: 'router-error',
                    }
                  : messageItem
              ),
            }
          : session
      ),
    }));
  } finally {
    setProcessing(false);
  }
};

export const generateImage = async (prompt: string) => {
  const { addMessage, setProcessing } = useChatStore.getState();
  setProcessing(true);

  try {
    const response = await fetch(IMAGE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, steps: 4 }),
    });

    if (!response.ok) {
      throw new Error(await response.text());
    }

    const data = await response.json();
    const imagePayload = data.image ?? data.image_b64;
    if (!imagePayload) {
      throw new Error('The image service returned an empty payload.');
    }

    addMessage({
      role: 'assistant',
      content: imagePayload,
      type: 'image',
      model: 'sd_turbo',
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    addMessage({
      role: 'assistant',
      content: `Failed to generate image: ${message}`,
      type: 'text',
      model: 'image-error',
    });
  } finally {
    setProcessing(false);
  }
};

export const transcribeAudio = async (audioBlob: Blob): Promise<string> => {
  const formData = new FormData();
  formData.append('file', audioBlob, 'recording.wav');

  const response = await fetch(STT_URL, { method: 'POST', body: formData });
  if (!response.ok) {
    throw new Error(await response.text());
  }

  const data = await response.json();
  return data.text;
};

export const synthesizeSpeech = async (text: string) => {
  try {
    const response = await fetch(TTS_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'tts-1', input: text, voice: 'uk' }),
    });

    if (!response.ok) {
      return;
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.addEventListener('ended', () => URL.revokeObjectURL(url), { once: true });
    await audio.play();
  } catch {
    // Audio playback is optional.
  }
};
