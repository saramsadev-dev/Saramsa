const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  trailingSlash: true,

  // Set tracing root to this directory so standalone output is flat (not nested under saramsa-ai/)
  outputFileTracingRoot: path.resolve(__dirname),
  
  // Enable React strict mode
  reactStrictMode: true,
  
  // Configure images
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'res.cloudinary.com',
        port: '',
        pathname: '/**',
      },
    ],
  },
  
  // Webpack configuration for path aliases
  webpack: (config, { isServer }) => {
    // Add path aliases
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, 'src'),
    };
    
    // Important: return the modified config
    return config;
  },
  
  // Disable TypeScript type checking during build (handled by CI)
  typescript: {
    ignoreBuildErrors: true,
  },
  
  // Disable ESLint during build (handled by CI)
  eslint: {
    ignoreDuringBuilds: true,
  },
}

module.exports = nextConfig;
