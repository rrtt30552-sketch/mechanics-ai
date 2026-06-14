'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

type Tab = 'design' | 'selection' | 'bom' | 'dfma' | 'fmea';

const tabs: { key: Tab; icon: string; label: string }[] = [
  { key: 'design', icon: '📐', label: '设计建议' },
  { key: 'selection', icon: '🔧', label: '选型计算' },
  { key: 'bom', icon: '📋', label: 'BOM 分析' },
  { key: 'dfma', icon: '✅', label: 'DFMA' },
  { key: 'fmea', icon: '⚠️', label: 'FMEA' },
];

export default function EngineeringPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>('design');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [token, setToken] = useState('');

  // 设计建议
  const [designDesc, setDesignDesc] = useState('');
  const [designConstraints, setDesignConstraints] = useState('');
  const [designMaterial, setDesignMaterial] = useState('');

  // 选型
  const [compType, setCompType] = useState('轴承');
  const [compReqs, setCompReqs] = useState('');

  // BOM
  const [bomDesc, setBomDesc] = useState('');

  // DFMA
  const [dfmaDesc, setDfmaDesc] = useState('');
  const [dfmaProcess, setDfmaProcess] = useState('');

  // FMEA
  const [fmeaDesc, setFmeaDesc] = useState('');

  useEffect(() => {
    const saved = localStorage.getItem('mechai_token');
    if (!saved) {
      router.push('/login');
      return;
    }
    setToken(saved);
  }, [router]);

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
      if (res.status === 401) {
        localStorage.removeItem('mechai_token');
        router.push('/login');
        return;
      }
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
      case 'design':
        callAPI('/api/engineering/design-advice', {
          description: designDesc,
          constraints: designConstraints.split('\n').filter(Boolean),
          material_preference: designMaterial || undefined,
        });
        break;
      case 'selection':
        try {
          const reqs = compReqs ? JSON.parse(compReqs) : {};
          callAPI('/api/engineering/selection', { component_type: compType, requirements: reqs });
        } catch {
          setResult('工况要求格式错误，请用 JSON 格式，如：{"载荷": "10kN", "转速": "1500rpm"}');
        }
        break;
      case 'bom':
        callAPI('/api/engineering/bom', { assembly_description: bomDesc });
        break;
      case 'dfma':
        callAPI('/api/engineering/dfma', {
          component_description: dfmaDesc,
          manufacturing_process: dfmaProcess || undefined,
        });
        break;
      case 'fmea':
        callAPI('/api/engineering/fmea', { system_description: fmeaDesc });
        break;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <Link href="/" className="text-slate-600 hover:text-blue-600">← 返回</Link>
          <h1 className="text-xl font-bold text-slate-900">⚙️ 工程辅助</h1>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {!token && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6 text-amber-800">
            ⚠️ 请先 <Link href="/login" className="text-blue-600 underline">登录</Link> 后再使用工程辅助功能
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
          {activeTab === 'design' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">设计需求描述 *</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-24 resize-none"
                  placeholder="例：设计一个承受径向载荷5kN、转速1500rpm的减速器输出轴"
                  value={designDesc}
                  onChange={(e) => setDesignDesc(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">约束条件（每行一条）</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-20 resize-none"
                  placeholder="例：&#10;空间限制：轴向长度不超过200mm&#10;成本限制：总成本低于500元"
                  value={designConstraints}
                  onChange={(e) => setDesignConstraints(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">材料偏好（可选）</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="例：45号钢、40Cr"
                  value={designMaterial}
                  onChange={(e) => setDesignMaterial(e.target.value)}
                />
              </div>
            </div>
          )}

          {activeTab === 'selection' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">零部件类型 *</label>
                <select
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  value={compType}
                  onChange={(e) => setCompType(e.target.value)}
                >
                  <option value="轴承">轴承</option>
                  <option value="齿轮">齿轮</option>
                  <option value="电机">电机</option>
                  <option value="联轴器">联轴器</option>
                  <option value="密封件">密封件</option>
                  <option value="弹簧">弹簧</option>
                  <option value="气缸">气缸</option>
                  <option value="液压缸">液压缸</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">工况要求 (JSON 格式)</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-24 resize-none font-mono"
                  placeholder={'{"载荷": "10kN", "转速": "1500rpm", "工作温度": "80°C", "安装方式": "水平"}'}
                  value={compReqs}
                  onChange={(e) => setCompReqs(e.target.value)}
                />
                <p className="text-xs text-slate-400 mt-1">填写工况参数，帮助 AI 精准选型</p>
              </div>
            </div>
          )}

          {activeTab === 'bom' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">装配体描述 *</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-24 resize-none"
                  placeholder="例：单级圆柱齿轮减速器，输入功率7.5kW，传动比4，含输入轴、输出轴、齿轮副、箱体、轴承等"
                  value={bomDesc}
                  onChange={(e) => setBomDesc(e.target.value)}
                />
              </div>
            </div>
          )}

          {activeTab === 'dfma' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">零件/装配体描述 *</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-24 resize-none"
                  placeholder="例：铝合金壳体，壁厚3mm，含安装孔4个，密封槽2个"
                  value={dfmaDesc}
                  onChange={(e) => setDfmaDesc(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">制造工艺（可选）</label>
                <input
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="例：CNC铣削、压铸、3D打印"
                  value={dfmaProcess}
                  onChange={(e) => setDfmaProcess(e.target.value)}
                />
              </div>
            </div>
          )}

          {activeTab === 'fmea' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">系统描述 *</label>
                <textarea
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm h-24 resize-none"
                  placeholder="例：汽车变速箱传动系统，含齿轮组、轴承、同步器、壳体"
                  value={fmeaDesc}
                  onChange={(e) => setFmeaDesc(e.target.value)}
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
