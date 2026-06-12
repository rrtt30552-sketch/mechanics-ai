/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      // 代理 API 请求到 Nginx（生产）或直接到后端（开发）
      {
        source: '/api/users/:path*',
        destination: process.env.NEXT_PUBLIC_USER_SERVICE_URL || 'http://localhost:8001/api/users/:path*',
      },
      {
        source: '/api/documents/:path*',
        destination: process.env.NEXT_PUBLIC_KNOWLEDGE_SERVICE_URL || 'http://localhost:8002/api/documents/:path*',
      },
      {
        source: '/api/chat/:path*',
        destination: process.env.NEXT_PUBLIC_AGENT_SERVICE_URL || 'http://localhost:8003/api/chat/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
