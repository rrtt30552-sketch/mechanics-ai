'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export default function KnowledgePage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [token, setToken] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [successMsg, setSuccessMsg] = useState<string>('');

  useEffect(() => {
    const saved = localStorage.getItem('mechai_token');
    if (!saved) {
      router.push('/login');
      return;
    }
    setToken(saved);
  }, [router]);

  useEffect(() => {
    if (token) fetchDocuments();
  }, [token]);

  // 自动清除提示
  useEffect(() => {
    if (successMsg || error) {
      const t = setTimeout(() => { setSuccessMsg(''); setError(''); }, 3000);
      return () => clearTimeout(t);
    }
  }, [successMsg, error]);

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/documents/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        localStorage.removeItem('mechai_token');
        router.push('/login');
        return;
      }
      if (res.ok) {
        setDocuments(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    }
  };

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    setError('');

    let successCount = 0;
    let failCount = 0;

    for (const file of Array.from(files)) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name);

      try {
        const res = await fetch(`${API_BASE}/api/documents/upload`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });
        if (res.status === 401) {
          localStorage.removeItem('mechai_token');
          router.push('/login');
          return;
        }
        if (res.ok) {
          successCount++;
        } else {
          failCount++;
          const err = await res.json().catch(() => ({}));
          console.error(`Upload failed for ${file.name}:`, err);
        }
      } catch (err) {
        failCount++;
        console.error('Upload failed:', err);
      }
    }

    if (successCount > 0) setSuccessMsg(`成功上传 ${successCount} 个文档`);
    if (failCount > 0) setError(`${failCount} 个文档上传失败`);
    if (successCount > 0) await fetchDocuments();
    setUploading(false);
  };

  const handleDelete = async (docId: number, docTitle: string) => {
    if (!confirm(`确定要删除「${docTitle}」吗？此操作不可恢复。`)) return;
    try {
      const res = await fetch(`${API_BASE}/api/documents/${docId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setSuccessMsg('文档已删除');
        await fetchDocuments();
      } else {
        setError('删除失败');
      }
    } catch (err) {
      setError('删除失败，请检查网络');
    }
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
    pdf: '📄', docx: '📝', doc: '📝', xlsx: '📊', xls: '📊',
    pptx: '📑', ppt: '📑', dwg: '📐', txt: '📃',
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-slate-600 hover:text-blue-600">← 返回</Link>
            <h1 className="text-xl font-bold text-slate-900">📚 知识库管理</h1>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="file"
              id="fileInput"
              className="hidden"
              multiple
              accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.dwg,.txt"
              onChange={(e) => handleUpload(e.target.files)}
            />
            <button
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
              onClick={() => document.getElementById('fileInput')?.click()}
              disabled={uploading}
            >
              {uploading ? '上传中...' : '+ 上传文档'}
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Toast 提示 */}
        {successMsg && (
          <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-xl text-sm">
            ✅ {successMsg}
          </div>
        )}
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl text-sm">
            ❌ {error}
          </div>
        )}

        {/* Upload Zone */}
        <div
          className={`border-2 border-dashed rounded-2xl p-12 text-center mb-8 transition-all cursor-pointer ${
            dragOver ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-white hover:border-blue-300'
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => document.getElementById('fileInput')?.click()}
        >
          <div className="text-4xl mb-4">📁</div>
          <p className="text-lg font-medium text-slate-700 mb-2">
            {uploading ? '正在上传...' : '拖拽文件到此处，或点击选择文件'}
          </p>
          <p className="text-sm text-slate-500">支持 PDF、Word、Excel、PPT、CAD、TXT 等格式</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-xl p-4 border border-slate-200">
            <div className="text-2xl font-bold text-blue-600">{documents.length}</div>
            <div className="text-sm text-slate-500">文档总数</div>
          </div>
          <div className="bg-white rounded-xl p-4 border border-slate-200">
            <div className="text-2xl font-bold text-green-600">
              {documents.reduce((sum, d) => sum + d.chunk_count, 0)}
            </div>
            <div className="text-sm text-slate-500">知识切片</div>
          </div>
          <div className="bg-white rounded-xl p-4 border border-slate-200">
            <div className="text-2xl font-bold text-purple-600">
              {formatSize(documents.reduce((sum, d) => sum + d.file_size, 0))}
            </div>
            <div className="text-sm text-slate-500">总存储</div>
          </div>
        </div>

        {/* Document List */}
        {documents.length === 0 ? (
          <div className="text-center py-16 text-slate-500">
            <div className="text-5xl mb-4">📭</div>
            <p className="text-lg">还没有上传任何文档</p>
            <p className="text-sm mt-1">上传文档后，AI 将自动解析并建立知识索引</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-6 py-3 text-sm font-medium text-slate-600">文档</th>
                  <th className="text-left px-6 py-3 text-sm font-medium text-slate-600">类型</th>
                  <th className="text-left px-6 py-3 text-sm font-medium text-slate-600">大小</th>
                  <th className="text-left px-6 py-3 text-sm font-medium text-slate-600">切片</th>
                  <th className="text-left px-6 py-3 text-sm font-medium text-slate-600">上传时间</th>
                  <th className="text-right px-6 py-3 text-sm font-medium text-slate-600">操作</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{typeIcon[doc.file_type] || '📄'}</span>
                        <div>
                          <div className="font-medium text-slate-900">{doc.title}</div>
                          {doc.tags.length > 0 && (
                            <div className="flex gap-1 mt-1 flex-wrap">
                              {doc.tags.map((tag) => (
                                <span key={tag} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 uppercase">{doc.file_type}</td>
                    <td className="px-6 py-4 text-sm text-slate-600">{formatSize(doc.file_size)}</td>
                    <td className="px-6 py-4 text-sm text-slate-600">{doc.chunk_count}</td>
                    <td className="px-6 py-4 text-sm text-slate-500">
                      {new Date(doc.created_at).toLocaleDateString('zh-CN')}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        className="text-red-500 hover:text-red-700 hover:bg-red-50 px-3 py-1 rounded-lg text-sm transition-colors"
                        onClick={() => handleDelete(doc.id, doc.title)}
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
