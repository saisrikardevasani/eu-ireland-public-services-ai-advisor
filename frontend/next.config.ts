import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Forward /api/* calls to the FastAPI backend during development
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
