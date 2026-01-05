import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Note: Turbopack has issues with route groups (e.g., (homepage))
  // Using standard webpack bundler for now
};

export default nextConfig;
