/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // Environment variables
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
    WIDGET_BASE_URL: process.env.WIDGET_BASE_URL || 'http://localhost:3000/widgets',
  },
  
  // Image optimization
  images: {
    domains: [
      'drive.google.com',
      'drive.usercontent.google.com',
      'api.gbif.org',
      'images.gbif.org',
      'localhost'
    ],
    formats: ['image/webp', 'image/avif'],
  },
  
  // Redirects for widget embedding
  async redirects() {
    return [
      {
        source: '/embed/:widget',
        destination: '/widgets/:widget/embed',
        permanent: true,
      },
    ]
  },
  
  // Headers for widget embedding
  async headers() {
    return [
      {
        source: '/widgets/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'Content-Security-Policy',
            value: "frame-ancestors 'self' *.neonone.com fcos.org *.fcos.org;",
          },
        ],
      },
    ]
  },
  
  // Webpack configuration for widget building
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Client-side only configurations for widgets
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
      }
    }
    
    return config
  },
}

module.exports = nextConfig