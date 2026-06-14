'use client';

import Link from 'next/link';
import { useState } from 'react';

const features = [
  {
    icon: '📚',
    title: '知识库管理',
    desc: '上传 PDF/Word/Excel/PPT/CAD 文档，AI 自动解析、向量化存储',
    href: '/knowledge',
  },
  {
    icon: '🤖',
    title: 'AI 智能问答',
    desc: '基于 RAG 架构的专业问答，支持机械原理、材料选择、工艺建议',
    href: '/chat',
  },
  {
    icon: '📖',
    title: '学习辅助',
    desc: '课程辅导、习题生成、考研辅导、错题分析',
    href: '/learning',
  },
  {
    icon: '⚙️',
    title: '工程辅助',
    desc: '设计建议、选型计算、BOM 分析、DFMA/FMEA',
    href: '/engineering',
  },
  {
    icon: '🔍',
    title: '故障诊断',
    desc: '故障现象分析、原因排查、维修方案推荐',
    href: '/diagnosis',
  },
  {
    icon: '📊',
    title: '知识检索',
    desc: '基于向量语义搜索，快速定位知识库中的相关内容',
    href: '/knowledge',
  },
];

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-lg">
                M
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">MechAI</h1>
                <p className="text-xs text-slate-500 -mt-0.5">机械工程 AI 助手</p>
              </div>
            </div>
            <nav className="hidden md:flex items-center gap-6">
              <Link href="/chat" className="text-slate-600 hover:text-blue-600 font-medium transition-colors">
                AI 问答
              </Link>
              <Link href="/knowledge" className="text-slate-600 hover:text-blue-600 font-medium transition-colors">
                知识库
              </Link>
              <Link href="/learning" className="text-slate-600 hover:text-blue-600 font-medium transition-colors">
                学习
              </Link>
              <Link href="/engineering" className="text-slate-600 hover:text-blue-600 font-medium transition-colors">
                工程
              </Link>
              <Link href="/diagnosis" className="text-slate-600 hover:text-blue-600 font-medium transition-colors">
                诊断
              </Link>
              <Link
                href="/login"
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                登录
              </Link>
            </nav>
            <button
              className="md:hidden p-2 text-slate-600"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              ☰
            </button>
          </div>
        </div>
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-t border-slate-200 px-4 py-3 space-y-2">
            <Link href="/chat" className="block py-2 text-slate-700">AI 问答</Link>
            <Link href="/knowledge" className="block py-2 text-slate-700">知识库</Link>
            <Link href="/learning" className="block py-2 text-slate-700">学习</Link>
            <Link href="/engineering" className="block py-2 text-slate-700">工程</Link>
            <Link href="/diagnosis" className="block py-2 text-slate-700">诊断</Link>
            <Link href="/login" className="block py-2 text-blue-600 font-medium">登录</Link>
          </div>
        )}
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
              <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
              AI 驱动的机械工程知识平台
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 mb-6 leading-tight">
              你的<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">机械工程</span>AI 助手
            </h1>
            <p className="text-lg sm:text-xl text-slate-600 max-w-3xl mx-auto mb-10 leading-relaxed">
              面向机械专业学生、教师和工程师的智能知识平台。
              上传文档建立专属知识库，AI 精准回答专业问题，辅助学习与工程实践。
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/chat"
                className="bg-blue-600 text-white px-8 py-3.5 rounded-xl hover:bg-blue-700 transition-all shadow-lg shadow-blue-500/25 font-medium text-lg"
              >
                开始对话 →
              </Link>
              <Link
                href="/knowledge"
                className="bg-white text-slate-700 px-8 py-3.5 rounded-xl hover:bg-slate-50 transition-all border border-slate-200 shadow-sm font-medium text-lg"
              >
                上传文档
              </Link>
            </div>
          </div>
        </div>
        {/* Background decoration */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-gradient-to-r from-blue-400/20 to-indigo-400/20 rounded-full blur-3xl -z-10"></div>
      </section>

      {/* Features */}
      <section className="py-20 bg-white/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">核心功能</h2>
            <p className="text-slate-600 text-lg">六大模块，覆盖学习与工程全场景</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <Link
                key={f.title}
                href={f.href}
                className="group bg-white rounded-2xl p-6 border border-slate-200 hover:border-blue-300 hover:shadow-lg hover:shadow-blue-500/10 transition-all"
              >
                <div className="text-4xl mb-4">{f.icon}</div>
                <h3 className="text-xl font-bold text-slate-900 mb-2 group-hover:text-blue-600 transition-colors">
                  {f.title}
                </h3>
                <p className="text-slate-600 leading-relaxed">{f.desc}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="py-16 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold text-slate-900 mb-3">技术架构</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { name: 'Next.js', desc: '前端框架' },
              { name: 'FastAPI', desc: '后端服务' },
              { name: 'PostgreSQL', desc: '关系数据库' },
              { name: 'pgvector', desc: '向量检索' },
              { name: 'DeepSeek', desc: 'AI 大模型' },
              { name: 'RAG', desc: '检索增强生成' },
              { name: 'Docker', desc: '容器化部署' },
              { name: 'Redis', desc: '缓存与队列' },
            ].map((t) => (
              <div key={t.name} className="bg-white rounded-xl p-4 text-center border border-slate-200">
                <div className="font-bold text-slate-900">{t.name}</div>
                <div className="text-sm text-slate-500">{t.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
              M
            </div>
            <span className="text-white font-bold text-lg">MechAI</span>
          </div>
          <p className="text-sm">© 2026 MechAI Platform. 面向机械专业的 AI 知识助手。</p>
        </div>
      </footer>
    </div>
  );
}
