import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Performance optimizations
  reactStrictMode: false, // Disable for faster development
  compress: true, // Enable response compression
  images: {
    formats: ['image/avif', 'image/webp'], // Modern image formats
    deviceSizes: [640, 750, 828, 1080, 1200],
    minimumCacheTTL: 60, // Cache images for 60 seconds
  },
  // Empty turbopack config to silence warning
  turbopack: {},
};

export default nextConfig;
