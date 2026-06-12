import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'MechAI - 机械工程 AI 助手',
  description: '面向机械专业学生、教师和工程师的云端机械知识库 AI 助手',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}
