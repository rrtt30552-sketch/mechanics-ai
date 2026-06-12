'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const TOPICS = [
  { key: '课程辅导', icon: '📖', label: '课程辅导', desc: '机械原理、材料力学等核心课程讲解', color: 'blue' },
  { key: '习题生成', icon: '✏️', label: '习题生成', desc: 'AI 自动生成练习题并批改', color: 'green' },
  { key: '考研辅导', icon: '🎓', label: '考研辅导', desc: '专业课复习、真题解析、重点梳理', color: 'purple' },
  { key: '错题分析', icon: '❌', label: '错题分析', desc: '分析错误原因，推荐巩固练习', color: 'red' },
] as const;

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; activeBg: string; activeBorder: string }> = {
  blue: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', activeBg: 'bg-blue-600', activeBorder: 'border-blue-600' },
  green: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', activeBg: 'bg-green-600', activeBorder: 'border-green-600' },
  purple: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700', activeBg: 'bg-purple-600', activeBorder: 'border-purple-600' },
  red: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', activeBg: 'bg-red-600', activeBorder: 'border-red-600' },
};

const PLACEHOLDERS: Record<string, string> = {
  '课程辅导': '例如：解释一下什么是应力集中？齿轮传动的失效形式有哪些？',
  '习题生成': '例如：出 3 道材料力学的计算题，难度中等',
  '考研辅导': '例如：哈工大机械原理考研重点有哪些？帮我梳理齿轮系传动比的考点',
  '错题分析': '例如：我的答案是 σ=200MPa，正确答案是 σ=150MPa，帮我分析错在哪里',
};

export default function LearningPage() {
  const [topic, setTopic] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const getToken = () => localStorage.getItem('token');

  const selectTopic = (t: string) => {
    setTopic(t);
    setMessages([]);
    setConversationId(null);
  };

  const sendMessage = async () => {
    if (!input.trim() || loading || !topic) return;

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
      const res = await fetch('http://localhost:8000/api/learning/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          topic,
          message: userMsg.content,
          conversation_id: conversationId,
        }),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error('请求失败');

      const assistantId = Date.now() + 1;
      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: 'assistant', content: '', timestamp: new Date() },
      ]);

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';

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
              if (parsed.type === 'content') {
                fullContent += parsed.content;
                setMessages((prev) =>
                  prev.map((m) => (m.id === assistantId ? { ...m, content: fullContent } : m))
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

  // Topic selection view
  if (!topic) {
    return (
      <div className="min-h-screen bg-slate-50">
        <header className="bg-white border-b border-slate-200 px-4 py-3">
          <div className="max-w-7xl mx-auto flex items-center gap-4">
            <Link href="/" className="text-slate-600 hover:text-blue-600 transition-colors">← 返回</Link>
            <h1 className="text-xl font-bold text-slate-900">📖 学习辅助</h1>
          </div>
        </header>
        <div className="max-w-4xl mx-auto px-4 py-12">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-slate-900 mb-3">选择学习模式</h2>
            <p className="text-slate-500">AI 助手将根据所选模式，提供针对性的学习辅导</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {TOPICS.map((t) => {
              const c = COLOR_MAP[t.color];
              return (
                <button
                  key={t.key}
                  onClick={() => selectTopic(t.key)}
                  className={`${c.bg} border-2 ${c.border} rounded-2xl p-6 text-left hover:shadow-lg transition-all hover:scale-[1.02] group`}
                >
                  <div className="text-4xl mb-3">{t.icon}</div>
                  <h3 className={`text-xl font-bold ${c.text} mb-2`}>{t.label}</h3>
                  <p className="text-slate-600 text-sm">{t.desc}</p>
                  <div className={`mt-4 inline-block ${c.activeBg} text-white text-sm px-4 py-1.5 rounded-full font-medium group-hover:opacity-90`}>
                    开始使用 →
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // Chat view
  const currentTopic = TOPICS.find((t) => t.key === topic)!;
  const c = COLOR_MAP[currentTopic.color];

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
          className="m-4 bg-slate-700 hover:bg-slate-600 text-white py-2.5 px-4 rounded-lg font-medium transition-colors text-sm"
          onClick={() => { setTopic(null); setMessages([]); setConversationId(null); }}
        >
          ← 切换模式
        </button>
        <div className="px-4 py-2">
          <div className={`${c.bg} ${c.border} border rounded-lg p-3`}>
            <div className="text-2xl mb-1">{currentTopic.icon}</div>
            <div className={`font-bold ${c.text}`}>{currentTopic.label}</div>
            <div className="text-xs text-slate-500 mt-1">{currentTopic.desc}</div>
          </div>
        </div>
        <div className="flex-1" />
        <div className="p-3 border-t border-slate-700 space-y-1">
          <Link href="/learning" className="flex items-center gap-2 px-3 py-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 text-sm">
            📖 学习辅助
          </Link>
          <Link href="/engineering" className="flex items-center gap-2 px-3 py-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 text-sm">
            ⚙️ 工程辅助
          </Link>
          <Link href="/knowledge" className="flex items-center gap-2 px-3 py-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 text-sm">
            📚 知识库
          </Link>
          <Link href="/" className="flex items-center gap-2 px-3 py-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 text-sm">
            🏠 首页
          </Link>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col">
        {/* Mobile header */}
        <div className="md:hidden bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
          <button onClick={() => { setTopic(null); setMessages([]); }} className="text-slate-600 text-sm">← 返回</button>
          <span className="font-bold text-slate-900">{currentTopic.icon} {currentTopic.label}</span>
          <button onClick={() => { setMessages([]); setConversationId(null); }} className="text-blue-600 text-sm">新对话</button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 max-w-4xl mx-auto w-full">
          {messages.length === 0 && (
            <div className="text-center py-16">
              <div className="text-6xl mb-4">{currentTopic.icon}</div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">{currentTopic.label}</h2>
              <p className="text-slate-500 mb-8">{currentTopic.desc}</p>
              <div className="max-w-lg mx-auto">
                <div className="bg-white rounded-2xl border border-slate-200 p-4 text-left">
                  <div className="text-sm text-slate-500 mb-2">💡 试试这样问：</div>
                  <div className="text-sm text-slate-700">{PLACEHOLDERS[topic]}</div>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-6">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? `${c.activeBg} text-white`
                      : 'bg-white border border-slate-200 text-slate-900'
                  }`}
                >
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {msg.content}
                    {loading && msg.role === 'assistant' && msg.content === '' && (
                      <span className="inline-block animate-pulse">●</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-slate-200 bg-white px-4 py-4">
          <div className="max-w-4xl mx-auto flex gap-3">
            <textarea
              className="flex-1 resize-none border border-slate-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 max-h-32"
              rows={1}
              placeholder={PLACEHOLDERS[topic]}
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
                className={`px-6 py-3 ${c.activeBg} text-white rounded-xl hover:opacity-90 transition-colors text-sm font-medium disabled:opacity-50`}
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
