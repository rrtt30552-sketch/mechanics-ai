'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

type Tab = 'fault' | 'vibration' | 'wear' | 'maintenance';

const tabs: { key: Tab; icon: string; label: string }[] = [
  { key: 'fault', icon: '🔍', label: '故障诊断' },
  { key: 'vibration', icon: '📊', label: '振动分析' },
  { key: 'wear', icon: '⚙️', label: '磨损分析' },
  { key: 'maintenance', icon: '🛠️', label: '维护计划' },
];

export default function DiagnosisPage() {
  const [activeTab, setActiveTab] = useState<Tab>('fault');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [token, setToken] = useState('');

  // 故障诊断
  const [faultEquip, setFaultEquip] = useState('');
  const [faultSymptoms, setFaultSymptoms] = useState('');
  const [faultHistory, setFaultHistory] = useState('');

  // 振动分析
  const [vibEquip, setVibEquip] = useState('');
  const [vibData, setVibData] = useState('');
  const [vibFreq, setVibFreq] = useState('');

  // 磨损分析
  const [wearComp, setWearComp] = useState('');
  const [wearType, setWearType] = useState('磨粒磨损');
  const [wearSeverity, setWearSeverity] = useState('moderate');
  const [wearEnv, setWearEnv] = useState('');

  // 维护计划
  const [maintEquip, setMaintEquip] = useState('');
  const [maintAge, setMaintAge] = useState('');
  const [maintCriticality, setMaintCriticality] = useState('medium');
  const [maintIssues, setMaintIssues] = useState('');

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
      case 'fault':
        callAPI('/api/diagnosis/fault', {
          equipment: faultEquip,
          symptoms: faultSymptoms.split('\n').filter(Boolean),
          history: faultHistory || undefined,
        });
        break;
      case 'vibration':
        callAPI('/api/diagnosis/vibration', {
          equipment: vibEquip,
          vibration_data: vibData || undefined,
          frequency_info: vibFreq || undefined,
        });
        break;
      case 'wear':
        callAPI('/api/diagnosis/wear', {
          component: wearComp,
          wear_type: wearType,
          severity: wearSeverity,
          operating_env: wearEnv || undefined,
        });
        break;
      case 'maintenance':
        callAPI('/api/diagnosis/maintenance-plan', {
          equipment: maintEquip,
          equipment_age: maintAge || undefined,
          criticality: maintCriticality,
          current_issues: maintIssues.split('\n').filter(Boolean),
        });
        break;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <Link href="/" className="text-slate-600 hover:text-blue-600">← 返回</Link>
          <h1 className="text-xl font-bold text-slate-900">🔍 故障诊断</h1>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {!token && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6 text-amber-800">
            ⚠️ 请先 <Link href="/login" className="text-blue-600 underline">登录</Link> 后再使用故障诊断功能
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

        {/* Form */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-6">
          {activeTab === 'fault' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">设备类型 *</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="例：三相异步电机、离心泵、数控机床主轴"
                  value={faultEquip}
                  onChange={(e) => setFaultEquip(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">故障现象（每行一条）*</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-24 resize-none"
                  placeholder="例：&#10;运行时异常振动&#10;轴承温度偏高（85°C）&#10;有异响"
                  value={faultSymptoms}
                  onChange={(e) => setFaultSymptoms(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">历史维修记录（可选）</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-16 resize-none"
                  placeholder="例：3个月前更换过轴承，3000小时前做过大修"
                  value={faultHistory}
                  onChange={(e) => setFaultHistory(e.target.value)}
                />
              </div>
            </div>
          )}

          {activeTab === 'vibration' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">设备类型 *</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="例：风机、压缩机、泵"
                  value={vibEquip}
                  onChange={(e) => setVibEquip(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">振动数据描述</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-20 resize-none"
                  placeholder="例：水平方向振动速度12mm/s，垂直方向8mm/s，轴向3mm/s"
                  value={vibData}
                  onChange={(e) => setVibData(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">频率特征</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="例：1X频率为主，2X分量较小，无明显高次谐波"
                  value={vibFreq}
                  onChange={(e) => setVibFreq(e.target.value)}
                />
              </div>
            </div>
          )}

          {activeTab === 'wear' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">磨损零件 *</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="例：液压缸活塞杆、齿轮齿面、轴承滚道"
                  value={wearComp}
                  onChange={(e) => setWearComp(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">磨损类型</label>
                  <select className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" value={wearType} onChange={(e) => setWearType(e.target.value)}>
                    <option value="磨粒磨损">磨粒磨损</option>
                    <option value="粘着磨损">粘着磨损</option>
                    <option value="疲劳磨损">疲劳磨损</option>
                    <option value="腐蚀磨损">腐蚀磨损</option>
                    <option value="微动磨损">微动磨损</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">严重程度</label>
                  <select className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" value={wearSeverity} onChange={(e) => setWearSeverity(e.target.value)}>
                    <option value="light">轻微</option>
                    <option value="moderate">中等</option>
                    <option value="severe">严重</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">工作环境（可选）</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="例：高温（200°C）、粉尘环境、腐蚀性介质"
                  value={wearEnv}
                  onChange={(e) => setWearEnv(e.target.value)}
                />
              </div>
            </div>
          )}

          {activeTab === 'maintenance' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">设备类型 *</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="例：CNC加工中心、注塑机、空压机"
                  value={maintEquip}
                  onChange={(e) => setMaintEquip(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">设备年龄</label>
                  <input
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                    placeholder="例：5年 / 8000小时"
                    value={maintAge}
                    onChange={(e) => setMaintAge(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">重要程度</label>
                  <select className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" value={maintCriticality} onChange={(e) => setMaintCriticality(e.target.value)}>
                    <option value="low">低 - 非关键设备</option>
                    <option value="medium">中 - 一般设备</option>
                    <option value="high">高 - 关键设备</option>
                    <option value="critical">极高 - 核心设备</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">当前问题（每行一条，可选）</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-20 resize-none"
                  placeholder="例：&#10;主轴精度下降&#10;液压系统偶尔报警"
                  value={maintIssues}
                  onChange={(e) => setMaintIssues(e.target.value)}
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

        {/* Result */}
        {result && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6">
            <h3 className="text-lg font-bold text-slate-900 mb-4">📋 诊断结果</h3>
            <div className="prose prose-slate max-w-none whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
              {result}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
