'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [form, setForm] = useState({ username: '', password: '', email: '', full_name: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const url = mode === 'login' ? '/api/users/login' : '/api/users/register';
      const body =
        mode === 'login'
          ? { username: form.username, password: form.password }
          : {
              username: form.username,
              password: form.password,
              email: form.email,
              full_name: form.full_name,
            };

      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: '请求失败' }));
        throw new Error(data.detail || '请求失败');
      }

      const data = await res.json();

      if (mode === 'login') {
        // 存储 JWT token
        localStorage.setItem('token', data.access_token);
        // 跳转到聊天页
        window.location.href = '/chat';
      } else {
        setMode('login');
        setError('注册成功！请登录');
      }
    } catch (err: any) {
      setError(err.message || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-lg">
              M
            </div>
            <span className="text-xl font-bold text-slate-900">MechAI</span>
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">
            {mode === 'login' ? '登录' : '注册'}
          </h1>
          <p className="text-slate-500 mt-1">
            {mode === 'login' ? '欢迎回来' : '创建你的 MechAI 账号'}
          </p>
        </div>

        {error && (
          <div
            className={`mb-4 p-3 rounded-lg text-sm ${
              error.includes('成功') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
            }`}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">用户名</label>
            <input
              type="text"
              className="w-full border border-slate-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              required
            />
          </div>

          {mode === 'register' && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">邮箱</label>
                <input
                  type="email"
                  className="w-full border border-slate-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">姓名</label>
                <input
                  type="text"
                  className="w-full border border-slate-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">密码</label>
            <input
              type="password"
              className="w-full border border-slate-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? '处理中...' : mode === 'login' ? '登录' : '注册'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-500">
          {mode === 'login' ? (
            <>
              没有账号？{' '}
              <button className="text-blue-600 hover:underline font-medium" onClick={() => setMode('register')}>
                注册
              </button>
            </>
          ) : (
            <>
              已有账号？{' '}
              <button className="text-blue-600 hover:underline font-medium" onClick={() => setMode('login')}>
                登录
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
