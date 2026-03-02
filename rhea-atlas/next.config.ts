import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ['three', '@react-three/fiber', '@react-three/drei'],
  eslint: { ignoreDuringBuilds: true },
  outputFileTracingRoot: __dirname,
  async redirects() {
    return [
      {
        source: '/',
        destination: '/cc',
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
