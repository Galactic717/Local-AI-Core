import React, { useRef, useState } from 'react';
import { Command, Image as ImageIcon, Loader2, Mic, Paperclip, Send, Square, X } from 'lucide-react';

import { streamChat, transcribeAudio } from '../api/client';
import { useChatStore } from '../store/useChatStore';

export const InputArea: React.FC = () => {
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [attachedImage, setAttachedImage] = useState<string | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addMessage = useChatStore((state) => state.addMessage);
  const isProcessing = useChatStore((state) => state.isProcessing);
  const setProcessing = useChatStore((state) => state.setProcessing);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (event) => {
        audioChunks.current.push(event.data);
      };

      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        setProcessing(true);
        try {
          const text = await transcribeAudio(audioBlob);
          setInput(text);
        } catch (error) {
          console.error('STT failed:', error);
        } finally {
          setProcessing(false);
        }
      };

      mediaRecorder.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      mediaRecorder.current.stream.getTracks().forEach((track) => track.stop());
    }
  };

  const handleSend = async () => {
    if ((!input.trim() && !attachedImage) || isProcessing) {
      return;
    }

    const userText = input.trim() || 'Please analyze this image.';
    const imagePayload = attachedImage ? attachedImage.replace(/^data:image\/[a-z]+;base64,/, '') : undefined;
    
    setInput('');
    setAttachedImage(null);

    addMessage({
      role: 'user',
      content: userText,
      type: 'text',
      image_b64: imagePayload,
    });

    await streamChat(userText);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      setAttachedImage(event.target?.result as string);
    };
    reader.readAsDataURL(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="relative border-t border-codex-border bg-codex-bg/80 p-6 backdrop-blur-xl">
      <div className="mx-auto max-w-4xl">
        <div className="group relative overflow-hidden rounded-2xl border border-codex-border shadow-2xl transition-all focus-within:border-codex-accent/50 focus-within:shadow-[0_0_30px_rgba(88,166,255,0.1)]">
          <div className="absolute left-4 top-4 text-codex-text/20">
            <Command size={18} />
          </div>

          {attachedImage && (
            <div className="absolute left-12 top-4 flex items-center gap-2">
              <div className="relative h-16 w-16 overflow-hidden rounded-lg border border-codex-border shadow-md">
                <img src={attachedImage} alt="Preview" className="h-full w-full object-cover" />
                <button
                  onClick={() => setAttachedImage(null)}
                  className="absolute right-1 top-1 rounded-full bg-black/50 p-1 text-white hover:bg-red-500/80"
                >
                  <X size={10} />
                </button>
              </div>
            </div>
          )}

          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) =>
              event.key === 'Enter' && !event.shiftKey && (event.preventDefault(), handleSend())
            }
            placeholder={isRecording ? 'Listening to your command...' : attachedImage ? 'Ask a question about this image...' : 'Ask anything, attach photos, run commands, or use /image...'}
            className={`min-h-[60px] max-h-[200px] w-full resize-none bg-codex-panel/50 py-4 pr-48 text-[14px] placeholder:text-codex-text/20 focus:outline-none ${attachedImage ? 'pl-[120px]' : 'pl-12'}`}
            rows={1}
          />

          <input type="file" accept="image/*" hidden ref={fileInputRef} onChange={handleFileChange} />

          <div className="absolute bottom-3 right-3 flex items-center gap-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-codex-text/40 transition-all hover:text-codex-accent"
              title="Attach Image"
            >
              <Paperclip size={18} />
            </button>
            <button
              onClick={() => setInput('/image ')}
              className="p-2 text-codex-text/40 transition-all hover:text-codex-purple"
              title="Image Mode"
            >
              <ImageIcon size={18} />
            </button>
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`rounded-lg p-2 transition-all ${
                isRecording
                  ? 'animate-pulse bg-red-500/10 text-red-500'
                  : 'text-codex-text/40 hover:bg-codex-cyan/10 hover:text-codex-cyan'
              }`}
            >
              {isRecording ? <Square size={18} /> : <Mic size={18} />}
            </button>
            <div className="mx-1 h-6 w-[1px] bg-codex-border" />
            <button
              onClick={handleSend}
              disabled={isProcessing || (!input.trim() && !attachedImage)}
              className="flex items-center gap-2 rounded-xl bg-codex-accent px-4 py-2 text-[12px] font-bold text-codex-bg transition-all active:scale-95 hover:bg-white disabled:opacity-30"
            >
              {isProcessing ? <Loader2 size={16} className="animate-spin" /> : <>SEND <Send size={14} /></>}
            </button>
          </div>
        </div>

        <div className="mt-3 flex justify-between px-2">
          <div className="text-[9px] font-bold uppercase tracking-[0.2em] text-codex-text/40">
            Secure Local Environment | v1.7.0
          </div>
          <div className="text-[9px] font-bold uppercase tracking-[0.2em] text-codex-accent/60">
            Agent Tools Active
          </div>
        </div>
      </div>
    </div>
  );
};
