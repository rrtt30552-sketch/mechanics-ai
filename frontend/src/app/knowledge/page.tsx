'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Document {
  id: number;
  title: string;
  file_type: string;
  file_size: number;
  category: string | null;
  tags: string[];
  chunk_count: number;
  created_at: string;
}

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState('');

  const getToken = () => localStorage.getItem('token');

  useEffect(() => {
    const token = getToken();
    if (!token) {
      window.location.href = '/login';
      return;
    }
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    const token = getToken();
    try {
      const res = await fetch('http://localhost:8000/api/documents/', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.status === 401) {
        window.location.href = '/login';
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    }
  };

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    setError('');

    const token = getToken();

    for (const file of Array.from(files)) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name);

      try {
        const res = await fetch('http://localhost:8000/api/documents/upload', {
          method: 'POST',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        });
        if (res.ok) {
          await fetchDocuments();
        } else {
          const data = await res.json().catch(() => ({ detail: '上传失败' }));
          setError(`${file.name}: ${data.detail || '上传失败'}`);
        }
      } catch (err) {
        setError(`${file.name}: 上传出错`);
      }
    }
    setUploading(false);
  };

  const handleDelete = async (docId: number) => {
    if (!confirm('确定要删除这个文档吗？')) return;
    const token = getToken();
    try {
      const res = await fetch(`http://localhost:8000/api/documents/${docId}`, {
        method: 'DELETE',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        await fetchDocuments();
      }
    } catch {}
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleUpload(e.dataTransfer.files);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const typeIcon: Record<string, string> = {
    pdf: '📄',
    docx: '📝',
    doc: '📝',
    xlsx: '📊',
    xls: '📊',
    pptx: '📑',
    ppt: '📑',
    dwg: '📐',
    txt: '📃',
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-slate-600 hover:text-blue-600">
              ← 返回
            </Link>
            <h1 className="text-xl font-bold text-slate-900">📚 知识库管理</h1>
          </div>
          <Link
            href="/chat"
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            去问答 →
          </Link>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Upload Zone */}
        <div
          className={`border-2 border-dashed rounded-xl p-8 text-center mb-6 transition-colors ${
            dragOver
              ? 'border-blue-500 bg-blue-50'
              : 'border-slate-300 bg-white hover:border-blue-400'
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <div className="text-4xl mb-3">📁</div>
          <p className="text-slate-700 font-medium mb-1">
            拖拽文件到此处上传
          </p>
          <p className="text-slate-400 text-sm mb-4">
            支持 PDF、Word、Excel、PPT、TXT 格式
          </p>
          <label className="inline-block cursor-pointer">
            <span className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
              {uploading ? '上传中...' : '选择文件'}
            </span>
            <input
              type="file"
              className="hidden"
              multiple
              accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt"
              onChange={(e) => handleUpload(e.target.files)}
              disabled={uploading}
            />
          </label>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">
            {error}
          </div>
        )}

        {/* Document List */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 bg-slate-50">
            <h2 className="font-medium text-slate-900">
              已上传文档 ({documents.length})
            </h2>
          </div>

          {documents.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <p>还没有上传任何文档</p>
              <p className="text-sm mt-1">上传文档后，AI 问答会基于这些文档进行回答</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="px-4 py-3 flex items-center justify-between hover:bg-slate-50"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{typeIcon[doc.file_type] || '📄'}</span>
                    <div>
                      <p className="font-medium text-slate-900 text-sm">{doc.title}</p>
                      <p className="text-xs text-slate-400">
                        {doc.file_type.toUpperCase()} · {formatSize(doc.file_size)} ·{' '}
                        {doc.chunk_count} 个片段
                        {doc.category && ` · ${doc.category}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">
                      {new Date(doc.created_at).toLocaleDateString('zh-CN')}
                    </span>
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="text-red-400 hover:text-red-600 text-sm px-2 py-1 rounded"
                    >
                      删除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tips */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4">
          <h3 className="font-medium text-blue-900 mb-2">💡 使用提示</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• 上传文档后，系统会自动解析、分块并生成向量索引</li>
            <li>• 在 <Link href="/chat" className="underline font-medium">AI 问答</Link> 中提问时，会自动检索知识库中的相关内容</li>
            <li>• 支持 PDF、Word、Excel、PPT、TXT 等格式</li>
            <li>• 文档内容越专业，AI 回答越准确</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
