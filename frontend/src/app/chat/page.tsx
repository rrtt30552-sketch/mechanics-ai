'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface Message {
  id: number | string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface Conversation {
  id: number;
  title: string;
  updated_at: string;
}

interface ModelInfo {
  key: string;
  name: string;
  description: string;
  max_tokens: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [token, setToken] = useState<string>('');
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('deepseek');
  const [showModelPicker, setShowModelPicker] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load token
  useEffect(() => {
    const saved = localStorage.getItem('mechai_token');
    if (saved) setToken(saved);
    const savedModel = localStorage.getItem('mechai_model');
    if (savedModel) setSelectedModel(savedModel);
  }, []);

  // Load models
  useEffect(() => {
    if (!token) return;
    fetch(`${API_BASE}/api/chat/models`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.ok ? r.json() : [])
      .then((data) => {
        setModels(data);
        // If saved model not in list, pick first available
        if (data.length > 0 && !data.find((m: ModelInfo) => m.key === selectedModel)) {
          setSelectedModel(data[0].key);
        }
      })
      .catch(() => {});
  }, [token]);

  // Load conversation list
  const loadConversations = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/chat/conversations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setConversations(await res.json());
    } catch {}
  }, [token]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Load messages for a conversation
  const loadMessages = async (convId: number) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/chat/conversations/${convId}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(
          data.map((m: any) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            timestamp: new Date(m.created_at),
          }))
        );
        setConversationId(convId);
      }
    } catch {}
  };

  const selectModel = (key: string) => {
    setSelectedModel(key);
    localStorage.setItem('mechai_model', key);
    setShowModelPicker(false);
  };

  // Stream chat
  const sendMessage = async () => {
    if (!input.trim() || loading || !token) return;

    const userMsg: Message = {
      id: Date.now(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    const userInput = input.trim();
    setInput('');
    setLoading(true);

    const assistantId = `stream-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: 'assistant', content: '', timestamp: new Date() },
    ]);

    try {
      const res = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: userInput,
          conversation_id: conversationId,
          model: selectedModel,
        }),
      });

      if (!res.ok) {
        if (res.status === 401) { logout(); return; }
        throw new Error('请求失败');
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const data = line.slice(6).trim();
            if (data === '[DONE]') continue;

            try {
              const parsed = JSON.parse(data);
              if (parsed.conversation_id && !conversationId) {
                setConversationId(parsed.conversation_id);
              }
              if (parsed.chunk) {
                fullContent += parsed.chunk;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId ? { ...m, content: fullContent } : m
                  )
                );
              }
            } catch {}
          }
        }
      }

      loadConversations();
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: '抱歉，请求出错了。请检查后端服务是否启动，以及 API Key 是否配置正确。' }
            : m
        )
      );
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

  const startNewChat = () => {
    setMessages([]);
    setConversationId(null);
  };

  const logout = () => {
    localStorage.removeItem('mechai_token');
    localStorage.removeItem('mechai_model');
    window.location.href = '/login';
  };

  const deleteConversation = async (convId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('确定删除这个对话吗？')) return;
    try {
      const res = await fetch(`${API_BASE}/api/chat/conversations/${convId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        if (conversationId === convId) {
          setMessages([]);
          setConversationId(null);
        }
        loadConversations();
      } else if (res.status === 401) {
        logout();
      }
    } catch {}
  };

  const currentModel = models.find((m) => m.key === selectedModel);

  if (!token) {
    return (
      <div className="flex h-screen bg-slate-50 items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🔒</div>
          <h2 className="text-2xl font-bold text-slate-900 mb-3">请先登录</h2>
          <p className="text-slate-600 mb-6">登录后才能使用 AI 对话功能</p>
          <Link href="/login" className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 transition-colors font-medium">
            去登录 →
          </Link>
        </div>
      </div>
    );
  }

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
          onClick={startNewChat}
        >
          + 新对话
        </button>
        <div className="flex-1 overflow-y-auto px-3 space-y-1">
          <div className="text-xs text-slate-500 uppercase tracking-wider px-2 py-2">历史对话</div>
          {conversations.length === 0 ? (
            <div className="text-sm text-slate-400 px-2 py-3">暂无历史对话</div>
          ) : (
            conversations.map((c) => (
              <div key={c.id} className="group relative">
                <button
                  className={`w-full text-left text-sm px-3 py-2.5 rounded-lg transition-colors truncate pr-8 ${
                    c.id === conversationId ? 'bg-blue-600/30 text-blue-200' : 'text-slate-300 hover:bg-slate-800'
                  }`}
                  onClick={() => loadMessages(c.id)}
                >
                  {c.title}
                </button>
                <button
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity px-1"
                  onClick={(e) => deleteConversation(c.id, e)}
                  title="删除对话"
                >
                  ✕
                </button>
              </div>
            ))
          )}
        </div>
        <div className="p-4 border-t border-slate-700 space-y-1">
          <Link href="/knowledge" className="flex items-center gap-2 text-slate-300 hover:text-white text-sm py-2">📚 知识库管理</Link>
          <Link href="/learning" className="flex items-center gap-2 text-slate-300 hover:text-white text-sm py-2">📖 学习辅助</Link>
          <Link href="/engineering" className="flex items-center gap-2 text-slate-300 hover:text-white text-sm py-2">⚙️ 工程辅助</Link>
          <Link href="/diagnosis" className="flex items-center gap-2 text-slate-300 hover:text-white text-sm py-2">🔍 故障诊断</Link>
          <button
            onClick={logout}
            className="flex items-center gap-2 text-slate-500 hover:text-red-400 text-sm py-2 w-full"
          >
            🚪 退出登录
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col">
        {/* Mobile header */}
        <header className="md:hidden bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
          <Link href="/" className="text-slate-600">← 返回</Link>
          <span className="font-bold text-slate-900">MechAI 对话</span>
          <button onClick={startNewChat} className="text-blue-600 text-sm">新对话</button>
        </header>

        {/* Model Selector Bar */}
        <div className="bg-white border-b border-slate-200 px-4 py-2 flex items-center gap-3">
          <span className="text-xs text-slate-500">模型:</span>
          <div className="relative">
            <button
              onClick={() => setShowModelPicker(!showModelPicker)}
              className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg text-sm transition-colors"
            >
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span className="font-medium text-slate-700">{currentModel?.name || selectedModel}</span>
              <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {showModelPicker && (
              <div className="absolute top-full left-0 mt-1 bg-white border border-slate-200 rounded-xl shadow-lg z-50 w-72 py-1">
                {models.length === 0 ? (
                  <div className="px-4 py-3 text-sm text-slate-500">暂无可用模型，请配置 API Key</div>
                ) : (
                  models.map((m) => (
                    <button
                      key={m.key}
                      onClick={() => selectModel(m.key)}
                      className={`w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors flex items-start gap-3 ${
                        m.key === selectedModel ? 'bg-blue-50' : ''
                      }`}
                    >
                      <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                        m.key === selectedModel ? 'bg-blue-500' : 'bg-slate-300'
                      }`}></span>
                      <div>
                        <div className="font-medium text-slate-800 text-sm">{m.name}</div>
                        <div className="text-xs text-slate-500">{m.description}</div>
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
          {currentModel && (
            <span className="text-xs text-slate-400 hidden sm:inline">{currentModel.description}</span>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto" onClick={() => setShowModelPicker(false)}>
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
                    onClick={() => setInput(q)}
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
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">
                      {msg.content || (loading && msg.role === 'assistant' ? '思考中...' : '')}
                    </div>
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 bg-slate-600 rounded-lg flex items-center justify-center text-white text-sm flex-shrink-0">
                      👤
                    </div>
                  )}
                </div>
              ))}
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
                {loading ? '...' : '发送'}
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-2 text-center">
              当前: {currentModel?.name || selectedModel} · MechAI 基于 RAG 架构，回答仅供参考
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
