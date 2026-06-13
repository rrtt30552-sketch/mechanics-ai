/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // API routing handled by nginx in Docker
  // No rewrites needed - frontend uses relative paths (/api/*)
};

module.exports = nextConfig;
