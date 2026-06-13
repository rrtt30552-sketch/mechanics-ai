/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // User service
      { source: '/api/users/:path*', destination: 'http://localhost:8001/api/users/:path*' },
      // Knowledge service
      { source: '/api/documents/:path*', destination: 'http://localhost:8002/api/documents/:path*' },
      // Agent service (chat)
      { source: '/api/chat/:path*', destination: 'http://localhost:8003/api/chat/:path*' },
      // Learning service
      { source: '/api/learning/:path*', destination: 'http://localhost:8005/api/learning/:path*' },
      // Engineering service
      { source: '/api/engineering/:path*', destination: 'http://localhost:8006/api/engineering/:path*' },
      // Diagnosis service
      { source: '/api/diagnosis/:path*', destination: 'http://localhost:8007/api/diagnosis/:path*' },
    ];
  },
};

module.exports = nextConfig;
