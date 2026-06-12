'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';

interface Source {
  doc_id: number;
  score: number;
  content: string;
}

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
}

interface Conversation {
  id: number;
  title: string;
  created_at: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    loadConversations();
  }, []);

  const getToken = () => localStorage.getItem('token');

  const loadConversations = async () => {
    const token = getToken();
    if (!token) return;
    try {
      const res = await fetch('http://localhost:8000/api/chat/conversations', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
      }
    } catch {}
  };

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

    const token = getToken();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch('http://localhost:8000/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: userMsg.content,
          conversation_id: conversationId,
        }),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error('请求失败');

      // 创建一条空的 assistant 消息，逐步填充
      const assistantId = Date.now() + 1;
      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: 'assistant', content: '', timestamp: new Date() },
      ]);

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      let sources: Source[] = [];

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value, { stream: true });
          const lines = text.split('\n');

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const data = line.slice(6).trim();
            if (data === '[DONE]') break;

            try {
              const parsed = JSON.parse(data);
              if (parsed.type === 'sources') {
                sources = parsed.sources;
              } else if (parsed.type === 'content') {
                fullContent += parsed.content;
                // 实时更新 assistant 消息
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId ? { ...m, content: fullContent, sources } : m
                  )
                );
              }
              if (parsed.conversation_id && !conversationId) {
                setConversationId(parsed.conversation_id);
              }
            } catch {}
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            role: 'assistant',
            content: '抱歉，请求出错了。请检查后端服务是否启动。',
            timestamp: new Date(),
          },
        ]);
      }
    } finally {
      setLoading(false);
      abortRef.current = null;
      loadConversations();
    }
  };

  const stopGeneration = () => {
    abortRef.current?.abort();
    setLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setConversationId(null);
  };

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 bg-slate-900 text-white flex-col">
        <div className="p-4 border-b border-slate-700">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-sm">
              M
            </div>
            <span className="font-bold text-lg">MechAI</span>
          </Link>
        </div>
        <button
          className="m-4 bg-blue-600 hover:bg-blue-700 text-white py-2.5 px-4 rounded-lg font-medium transition-colors"
          onClick={startNewChat}
        >
          + 新对话
        </button>
        <div className="flex-1 overflow-y-auto px-3 space-y-1">
          <div className="text-xs text-slate-500 uppercase tracking-wider px-2 py-2">
            历史对话
          </div>
          {conversations.map((conv) => (
            <button
              key={conv.id}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                conversationId === conv.id
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
              onClick={() => {
                setConversationId(conv.id);
                // TODO: load history
              }}
            >
              {conv.title || `对话 #${conv.id}`}
            </button>
          ))}
        </div>
        <div className="p-3 border-t border-slate-700">
          <Link
            href="/knowledge"
            className="flex items-center gap-2 px-3 py-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 text-sm"
          >
            📚 知识库管理
          </Link>
          <Link
            href="/"
            className="flex items-center gap-2 px-3 py-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 text-sm"
          >
            🏠 返回首页
          </Link>
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Mobile Header */}
        <div className="md:hidden bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
          <Link href="/" className="text-slate-600">
            ← 返回
          </Link>
          <span className="font-bold text-slate-900">AI 问答</span>
          <button onClick={startNewChat} className="text-blue-600 text-sm">
            新对话
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 max-w-4xl mx-auto w-full">
          {messages.length === 0 && (
            <div className="text-center py-20">
              <div className="text-6xl mb-6">🤖</div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">MechAI 机械工程助手</h2>
              <p className="text-slate-500 mb-8">
                基于 RAG 架构，结合你的知识库文档进行专业问答
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto">
                {[
                  '45号钢和40Cr有什么区别？',
                  '齿轮模数怎么选择？',
                  '液压系统压力不足怎么办？',
                  '淬火和回火的区别是什么？',
                ].map((q) => (
                  <button
                    key={q}
                    className="text-left px-4 py-3 bg-white border border-slate-200 rounded-xl hover:border-blue-300 hover:bg-blue-50 text-sm text-slate-700 transition-colors"
                    onClick={() => {
                      setInput(q);
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-6">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-slate-200 text-slate-900'
                  }`}
                >
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {msg.content}
                    {loading && msg.role === 'assistant' && msg.content === '' && (
                      <span className="inline-block animate-pulse">●</span>
                    )}
                  </div>

                  {/* 检索来源 */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-100">
                      <div className="text-xs text-slate-400 mb-1">📎 参考来源</div>
                      <div className="space-y-1">
                        {msg.sources.map((s, i) => (
                          <div key={i} className="text-xs text-slate-500 bg-slate-50 rounded px-2 py-1">
                            文档#{s.doc_id} [{(s.score * 100).toFixed(0)}%] {s.content.slice(0, 80)}...
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-200 bg-white px-4 py-4">
          <div className="max-w-4xl mx-auto flex gap-3">
            <textarea
              className="flex-1 resize-none border border-slate-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 max-h-32"
              rows={1}
              placeholder="输入你的机械工程问题..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            {loading ? (
              <button
                className="px-4 py-3 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-colors text-sm font-medium"
                onClick={stopGeneration}
              >
                停止
              </button>
            ) : (
              <button
                className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50"
                onClick={sendMessage}
                disabled={!input.trim()}
              >
                发送
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
