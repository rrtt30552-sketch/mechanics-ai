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

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await fetch('/api/documents/');
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

    for (const file of Array.from(files)) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name);

      try {
        const res = await fetch('/api/documents/upload', {
          method: 'POST',
          body: formData,
        });
        if (res.ok) {
          await fetchDocuments();
        }
      } catch (err) {
        console.error('Upload failed:', err);
      }
    }
    setUploading(false);
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
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              onClick={() => document.getElementById('fileInput')?.click()}
              disabled={uploading}
            >
              {uploading ? '上传中...' : '+ 上传文档'}
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Upload Zone */}
        <div
          className={`border-2 border-dashed rounded-2xl p-12 text-center mb-8 transition-all ${
            dragOver ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-white'
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <div className="text-4xl mb-4">📁</div>
          <p className="text-lg font-medium text-slate-700 mb-2">拖拽文件到此处上传</p>
          <p className="text-sm text-slate-500">支持 PDF、Word、Excel、PPT、CAD 等格式</p>
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
                  <th className="text-left px-6 py-3 text-sm font-medium text-slate-600">操作</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{typeIcon[doc.file_type] || '📄'}</span>
                        <div>
                          <div className="font-medium text-slate-900">{doc.title}</div>
                          {doc.tags.length > 0 && (
                            <div className="flex gap-1 mt-1">
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
                    <td className="px-6 py-4">
                      <button className="text-red-500 hover:text-red-700 text-sm">删除</button>
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
