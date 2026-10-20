import { useState, useCallback, useRef } from 'react';

function sessionId() {
  const key = 'egspec_session';
  let id = localStorage.getItem(key);
  if (!id) {
    id = 'sess_' + Math.random().toString(36).slice(2, 11);
    localStorage.setItem(key, id);
  }
  return id;
}

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [streaming, setStreaming] = useState(false);
  const [quickReplies, setQuickReplies] = useState([]);
  const abortRef = useRef(null);

  const send = useCallback(async (text) => {
    const q = (text || '').trim();
    if (!q || streaming) return;

    setMessages((m) => [...m, { role: 'user', content: q }]);
    setStreaming(true);

    const botIndex = { current: -1 };
    setMessages((m) => {
      botIndex.current = m.length;
      return [...m, { role: 'bot', content: '', sources: [] }];
    });

    try {
      const res = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId(),
          message: q,
          user_id: null,
          language: 'auto',
        }),
      });

      if (!res.ok || !res.body) throw new Error('Stream unavailable');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let answer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split('\n\n');
        buffer = blocks.pop() || '';

        for (const block of blocks) {
          const event = (block.match(/^event:\s*(.+)$/m) || [])[1];
          const raw = (block.match(/^data:\s*(.+)$/m) || [])[1];
          if (!raw) continue;
          let data;
          try {
            data = JSON.parse(raw);
          } catch {
            continue;
          }

          if (event === 'token' && data.text) {
            answer += data.text;
            setMessages((m) => {
              const next = [...m];
              const i = next.length - 1;
              if (next[i]?.role === 'bot') {
                next[i] = { ...next[i], content: answer };
              }
              return next;
            });
          } else if (event === 'complete') {
            if (data.quick_replies?.length) setQuickReplies(data.quick_replies);
            setMessages((m) => {
              const next = [...m];
              const i = next.length - 1;
              if (next[i]?.role === 'bot') {
                next[i] = {
                  ...next[i],
                  content: answer || data.answer || next[i].content,
                  sources: data.sources || [],
                };
              }
              return next;
            });
          } else if (event === 'error') {
            setMessages((m) => {
              const next = [...m];
              const i = next.length - 1;
              if (next[i]?.role === 'bot') {
                next[i] = {
                  ...next[i],
                  content: data.detail || 'Something went wrong. Please try again.',
                  error: true,
                };
              }
              return next;
            });
          }
        }
      }
    } catch (err) {
      setMessages((m) => {
        const next = [...m];
        const i = next.length - 1;
        if (next[i]?.role === 'bot') {
          next[i] = {
            ...next[i],
            content:
              'Connection error. Start the backend with: python main.py',
            error: true,
          };
        }
        return next;
      });
    } finally {
      setStreaming(false);
    }
  }, [streaming]);

  const reset = useCallback(() => {
    // A fresh chat must not inherit the previous server-side topic.
    localStorage.removeItem('egspec_session');
    setMessages([]);
    setQuickReplies([]);
  }, []);

  return { messages, streaming, quickReplies, send, reset };
}
