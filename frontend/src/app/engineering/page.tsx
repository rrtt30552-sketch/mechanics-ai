'use client';

import Link from 'next/link';

export default function EngineeringPage() {
  const modules = [
    {
      icon: '📐',
      title: '设计建议',
      desc: '根据工况参数推荐结构方案、材料选型、安全系数校核',
      status: '即将上线',
    },
    {
      icon: '🔧',
      title: '选型计算',
      desc: '轴承、电机、减速器、气缸等标准件选型计算',
      status: '即将上线',
    },
    {
      icon: '📋',
      title: 'BOM 分析',
      desc: '物料清单生成、成本估算、供应商推荐',
      status: '即将上线',
    },
    {
      icon: '🏭',
      title: '工艺路线',
      desc: '加工工艺规划、工序安排、工时估算',
      status: '即将上线',
    },
    {
      icon: '✅',
      title: 'DFMA',
      desc: '面向制造和装配的设计评审、优化建议',
      status: '即将上线',
    },
    {
      icon: '⚠️',
      title: 'FMEA',
      desc: '失效模式与影响分析、风险优先级评估',
      status: '即将上线',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <Link href="/" className="text-slate-600 hover:text-blue-600">← 返回</Link>
          <h1 className="text-xl font-bold text-slate-900">⚙️ 工程辅助</h1>
        </div>
      </header>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
