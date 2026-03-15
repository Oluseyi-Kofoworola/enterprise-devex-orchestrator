import { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg.content,
          history: messages.map((m) => ({ role: m.role, content: m.content })),
        }),
      });
      const data = await res.json();
      const assistantMsg: Message = {
        role: 'assistant',
        content: data.reply || 'No response',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Error: Could not reach AI service.', timestamp: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">smart-city-ai-operations-platform-extre AI Assistant</h1>
        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
          AI Powered
        </span>
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto bg-gray-50 rounded-lg border p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 py-12">
            <p className="text-lg">Welcome to smart-city-ai-operations-platform-extre AI Assistant</p>
            <p className="text-sm mt-2">Ask a question to get started.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[70%] rounded-lg px-4 py-2 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border text-gray-900'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              <p className={`text-xs mt-1 ${msg.role === 'user' ? 'text-blue-200' : 'text-gray-400'}`}>
                {new Date(msg.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-lg px-4 py-2 text-gray-500">
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="mt-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          className="flex-1 border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </div>
  );
}
