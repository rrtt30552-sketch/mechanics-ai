'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

type Tab = 'tutor' | 'exercises' | 'exam' | 'mistake';

const tabs: { key: Tab; icon: string; label: string }[] = [
  { key: 'tutor', icon: '📖', label: '课程辅导' },
  { key: 'exercises', icon: '✏️', label: '习题生成' },
  { key: 'exam', icon: '🎓', label: '考研辅导' },
  { key: 'mistake', icon: '❌', label: '错题分析' },
];

export default function LearningPage() {
  const [activeTab, setActiveTab] = useState<Tab>('tutor');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [token, setToken] = useState('');

  // 课程辅导
  const [topic, setTopic] = useState('');
  const [level, setLevel] = useState('undergraduate');
  const [question, setQuestion] = useState('');

  // 习题生成
  const [exTopic, setExTopic] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [exCount, setExCount] = useState(5);
  const [exType, setExType] = useState('choice');

  // 考研辅导
  const [examType, setExamType] = useState('考研');
  const [subjects, setSubjects] = useState('机械原理,机械设计,材料力学');

  // 错题分析
  const [mistakeQ, setMistakeQ] = useState('');
  const [mistakeA, setMistakeA] = useState('');
  const [correctA, setCorrectA] = useState('');

  useEffect(() => {
    const saved = localStorage.getItem('mechai_token');
    if (saved) setToken(saved);
  }, []);

  const callAPI = async (path: string, body: any) => {
    if (!token) {
      setResult('请先登录后再使用此功能');
      return;
    }
    setLoading(true);
    setResult('');
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data.reply || JSON.stringify(data, null, 2));
      } else {
        const err = await res.json().catch(() => ({}));
        setResult(`请求失败: ${err.detail || res.statusText}`);
      }
    } catch (e: any) {
      setResult(`网络错误: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => {
    switch (activeTab) {
      case 'tutor':
        callAPI('/api/learning/tutor', { topic, level, question: question || undefined });
        break;
      case 'exercises':
        callAPI('/api/learning/exercises', { topic: exTopic, difficulty, count: exCount, type: exType });
        break;
      case 'exam':
        callAPI('/api/learning/exam-prep', {
          exam_type: examType,
          subjects: subjects.split(',').map(s => s.trim()).filter(Boolean),
        });
        break;
      case 'mistake':
        callAPI('/api/learning/mistake-analysis', {
          question: mistakeQ,
          student_answer: mistakeA,
          correct_answer: correctA || undefined,
        });
        break;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <Link href="/" className="text-slate-600 hover:text-blue-600">← 返回</Link>
          <h1 className="text-xl font-bold text-slate-900">📖 学习辅助</h1>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {!token && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6 text-amber-800">
            ⚠️ 请先 <Link href="/login" className="text-blue-600 underline">登录</Link> 后再使用学习辅助功能
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => { setActiveTab(t.key); setResult(''); }}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm whitespace-nowrap transition-all ${
                activeTab === t.key
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25'
                  : 'bg-white text-slate-600 border border-slate-200 hover:border-blue-300'
              }`}
            >
              <span>{t.icon}</span> {t.label}
            </button>
          ))}
        </div>

        {/* Form Area */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-6">
          {activeTab === 'tutor' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">学习主题 *</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
                  placeholder="例：渐开线齿轮传动、液压系统、轴承选型"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">学习水平</label>
                <select
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  value={level}
                  onChange={(e) => setLevel(e.target.value)}
                >
                  <option value="undergraduate">本科</option>
                  <option value="graduate">研究生</option>
                  <option value="professional">工程实践</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">具体问题（可选）</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-20 resize-none"
                  placeholder="如果不填，将对主题进行全面讲解"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                />
              </div>
            </div>
          )}

          {activeTab === 'exercises' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">题目主题 *</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="例：材料力学弯曲应力、机械原理自由度计算"
                  value={exTopic}
                  onChange={(e) => setExTopic(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">难度</label>
                  <select className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                    <option value="easy">简单</option>
                    <option value="medium">中等</option>
                    <option value="hard">困难</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">题型</label>
                  <select className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" value={exType} onChange={(e) => setExType(e.target.value)}>
                    <option value="choice">选择题</option>
                    <option value="fill">填空题</option>
                    <option value="solve">计算题</option>
                    <option value="essay">论述题</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">数量</label>
                  <input
                    type="number"
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                    min={1} max={20}
                    value={exCount}
                    onChange={(e) => setExCount(Number(e.target.value))}
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'exam' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">考试类型</label>
                <select className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" value={examType} onChange={(e) => setExamType(e.target.value)}>
                  <option value="考研">考研</option>
                  <option value="期末">期末考试</option>
                  <option value="注册工程师">注册工程师</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">科目（逗号分隔）</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="机械原理,机械设计,材料力学"
                  value={subjects}
                  onChange={(e) => setSubjects(e.target.value)}
                />
              </div>
            </div>
          )}

          {activeTab === 'mistake' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">题目 *</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-20 resize-none"
                  placeholder="请描述题目内容"
                  value={mistakeQ}
                  onChange={(e) => setMistakeQ(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">你的答案 *</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-20 resize-none"
                  placeholder="你当时是怎么回答的"
                  value={mistakeA}
                  onChange={(e) => setMistakeA(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">正确答案（可选）</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="如果知道正确答案可以填写"
                  value={correctA}
                  onChange={(e) => setCorrectA(e.target.value)}
                />
              </div>
            </div>
          )}

          <button
            className="mt-4 bg-blue-600 text-white px-6 py-2.5 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
            onClick={handleSubmit}
            disabled={loading || !token}
          >
            {loading ? 'AI 分析中...' : '开始分析'}
          </button>
        </div>

        {/* Result Area */}
        {result && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6">
            <h3 className="text-lg font-bold text-slate-900 mb-4">📋 分析结果</h3>
            <div className="prose prose-slate max-w-none whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
              {result}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
