'use client';

import Link from 'next/link';

export default function LearningPage() {
  const modules = [
    {
      icon: '📖',
      title: '课程辅导',
      desc: '机械原理、机械设计、材料力学等核心课程知识讲解',
      status: '即将上线',
    },
    {
      icon: '✏️',
      title: '习题生成',
      desc: 'AI 根据知识点自动生成练习题，支持选择、填空、计算',
      status: '即将上线',
    },
    {
      icon: '🎓',
      title: '考研辅导',
      desc: '机械类考研专业课复习指导、真题解析、重点知识梳理',
      status: '即将上线',
    },
    {
      icon: '❌',
      title: '错题分析',
      desc: '记录错题、分析错误原因、推荐相关知识点强化练习',
      status: '即将上线',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <Link href="/" className="text-slate-600 hover:text-blue-600">← 返回</Link>
          <h1 className="text-xl font-bold text-slate-900">📖 学习辅助</h1>
        </div>
      </header>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {modules.map((m) => (
            <div key={m.title} className="bg-white rounded-2xl p-6 border border-slate-200 hover:shadow-lg transition-shadow">
              <div className="text-4xl mb-4">{m.icon}</div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">{m.title}</h3>
              <p className="text-slate-600 mb-4">{m.desc}</p>
              <span className="inline-block bg-amber-100 text-amber-700 text-sm px-3 py-1 rounded-full font-medium">
                {m.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
