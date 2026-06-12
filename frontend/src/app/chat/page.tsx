'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = {
      id: Date.now(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg.content,
          conversation_id: conversationId,
        }),
      });

      if (!res.ok) throw new Error('请求失败');

      const data = await res.json();
      setConversationId(data.conversation_id);

      const assistantMsg: Message = {
        id: data.message_id,
        role: 'assistant',
        content: data.reply,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errMsg: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: '抱歉，请求出错了。请检查后端服务是否启动。',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 bg-slate-900 text-white flex-col">
        <div className="p-4 border-b border-slate-700">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-sm">M</div>
            <span className="font-bold text-lg">MechAI</span>
          </Link>
        </div>
        <button
          className="m-4 bg-blue-600 hover:bg-blue-700 text-white py-2.5 px-4 rounded-lg font-medium transition-colors"
          onClick={() => {
            setMessages([]);
            setConversationId(null);
          }}
        >
          + 新对话
        </button>
        <div className="flex-1 overflow-y-auto px-3 space-y-1">
          <div className="text-xs text-slate-500 uppercase tracking-wider px-2 py-2">历史对话</div>
          {/* TODO: load conversation list */}
          <div className="text-sm text-slate-400 px-2 py-3">暂无历史对话</div>
        </div>
        <div className="p-4 border-t border-slate-700">
          <Link href="/knowledge" className="flex items-center gap-2 text-slate-300 hover:text-white text-sm py-2">
            📚 知识库管理
          </Link>
          <Link href="/learning" className="flex items-center gap-2 text-slate-300 hover:text-white text-sm py-2">
            📖 学习辅助
          </Link>
          <Link href="/engineering" className="flex items-center gap-2 text-slate-300 hover:text-white text-sm py-2">
            ⚙️ 工程辅助
          </Link>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col">
        {/* Mobile header */}
        <header className="md:hidden bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
          <Link href="/" className="text-slate-600">← 返回</Link>
          <span className="font-bold text-slate-900">MechAI 对话</span>
          <div className="w-8"></div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <div className="text-6xl mb-6">🤖</div>
              <h2 className="text-2xl font-bold text-slate-900 mb-3">MechAI 机械工程助手</h2>
              <p className="text-slate-600 max-w-md mb-8">
                我可以帮你解答机械设计、材料选型、加工工艺、故障诊断等专业问题。
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
                {[
                  '45号钢和40Cr有什么区别？',
                  '渐开线齿轮的模数怎么选？',
                  '液压系统压力不足怎么排查？',
                  '解释一下淬火和回火的区别',
                ].map((q) => (
                  <button
                    key={q}
                    className="text-left bg-white border border-slate-200 rounded-xl p-3 text-sm text-slate-700 hover:border-blue-300 hover:bg-blue-50 transition-all"
                    onClick={() => { setInput(q); }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                      AI
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-slate-200 text-slate-800'
                    }`}
                  >
                    <div className="markdown-body whitespace-pre-wrap text-sm leading-relaxed">
                      {msg.content}
                    </div>
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 bg-slate-600 rounded-lg flex items-center justify-center text-white text-sm flex-shrink-0">
                      👤
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex gap-4">
                  <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white text-sm font-bold">
                    AI
                  </div>
                  <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-slate-200 bg-white px-4 py-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3 items-end">
              <textarea
                className="flex-1 resize-none rounded-xl border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 max-h-32"
                rows={1}
                placeholder="输入你的问题... (Enter 发送, Shift+Enter 换行)"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
              />
              <button
                className="bg-blue-600 text-white px-5 py-3 rounded-xl hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={sendMessage}
                disabled={loading || !input.trim()}
              >
                发送
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-2 text-center">
              MechAI 基于 RAG 架构，回答基于你的知识库内容生成。仅供参考。
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
