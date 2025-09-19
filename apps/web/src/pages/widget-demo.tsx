import React from 'react';
import EmbeddableOrchidGallery from '../../../packages/ui/src/components/EmbeddableOrchidGallery';

const WidgetDemoPage = () => {
  const apiBaseUrl = process.env.NODE_ENV === 'production' 
    ? 'https://your-production-domain.replit.app'
    : 'http://localhost:5000';

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🌺 Orchid Continuum Widget Showcase
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Embeddable orchid collection widgets for the Five Cities Orchid Society. 
            Perfect for integration with Neon One CMS and other websites.
          </p>
        </div>

        <div className="space-y-12">
          {/* Basic Gallery Widget */}
          <section className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4">Basic Gallery Widget</h2>
            <p className="text-gray-600 mb-6">
              A simple gallery showing featured orchids from the collection.
            </p>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
              <EmbeddableOrchidGallery 
                apiBaseUrl={apiBaseUrl}
                limit={6}
                theme="light"
              />
            </div>
            <div className="mt-6">
              <h3 className="font-semibold mb-2">Code Example:</h3>
              <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`<!-- React Component -->
<EmbeddableOrchidGallery 
  apiBaseUrl="https://your-domain.replit.app"
  limit={6}
  theme="light"
/>

<!-- JavaScript Widget -->
<div data-orchid-widget data-limit="6" data-theme="light"></div>
<script src="https://your-domain.replit.app/static/orchid-widget.js"></script>`}
              </pre>
            </div>
          </section>

          {/* Dark Theme Widget */}
          <section className="bg-gray-900 rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4 text-white">Dark Theme Widget</h2>
            <p className="text-gray-300 mb-6">
              Perfect for websites with dark themes or modern design aesthetics.
            </p>
            <div className="border-2 border-dashed border-gray-600 rounded-lg p-4">
              <EmbeddableOrchidGallery 
                apiBaseUrl={apiBaseUrl}
                limit={4}
                theme="dark"
              />
            </div>
            <div className="mt-6">
              <h3 className="font-semibold mb-2 text-white">Code Example:</h3>
              <pre className="bg-gray-800 text-green-400 p-4 rounded text-sm overflow-x-auto">
{`<div data-orchid-widget data-limit="4" data-theme="dark"></div>`}
              </pre>
            </div>
          </section>

          {/* Genus-Specific Widget */}
          <section className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4">Genus-Specific Widget</h2>
            <p className="text-gray-600 mb-6">
              Display orchids from a specific genus - perfect for educational content.
            </p>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
              <EmbeddableOrchidGallery 
                apiBaseUrl={apiBaseUrl}
                limit={3}
                genus="Cattleya"
                theme="light"
              />
            </div>
            <div className="mt-6">
              <h3 className="font-semibold mb-2">Code Example:</h3>
              <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`<div data-orchid-widget 
     data-limit="3" 
     data-genus="Cattleya" 
     data-theme="light">
</div>`}
              </pre>
            </div>
          </section>

          {/* Compact Widget */}
          <section className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4">Compact Widget</h2>
            <p className="text-gray-600 mb-6">
              A smaller widget perfect for sidebars or limited space areas.
            </p>
            <div className="max-w-md border-2 border-dashed border-gray-300 rounded-lg p-4">
              <EmbeddableOrchidGallery 
                apiBaseUrl={apiBaseUrl}
                limit={2}
                theme="light"
                style={{ maxWidth: '400px' }}
              />
            </div>
            <div className="mt-6">
              <h3 className="font-semibold mb-2">Code Example:</h3>
              <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`<div data-orchid-widget 
     data-limit="2" 
     style="max-width: 400px;">
</div>`}
              </pre>
            </div>
          </section>

          {/* Integration Instructions */}
          <section className="bg-blue-50 rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4 text-blue-900">
              Integration with Neon One CMS
            </h2>
            <div className="prose max-w-none text-blue-800">
              <h3 className="text-lg font-semibold mb-3">Quick Setup (3 steps):</h3>
              <ol className="list-decimal list-inside space-y-2 mb-6">
                <li>Add the widget script to your website header</li>
                <li>Place the widget div where you want the gallery to appear</li>
                <li>Configure with data attributes for customization</li>
              </ol>

              <h3 className="text-lg font-semibold mb-3">Complete Code Example:</h3>
              <pre className="bg-white p-4 rounded border text-sm overflow-x-auto text-gray-800">
{`<!DOCTYPE html>
<html>
<head>
  <!-- Add to your website header -->
  <script src="https://your-domain.replit.app/static/orchid-widget.js"></script>
</head>
<body>
  <!-- Place anywhere in your content -->
  <div data-orchid-widget 
       data-limit="6" 
       data-theme="light" 
       data-genus="Cattleya">
  </div>
  
  <!-- Widget auto-initializes on page load -->
</body>
</html>`}
              </pre>

              <h3 className="text-lg font-semibold mb-3 mt-6">Available Options:</h3>
              <ul className="list-disc list-inside space-y-1">
                <li><code className="bg-white px-2 py-1 rounded">data-limit</code> - Number of orchids to display (default: 6)</li>
                <li><code className="bg-white px-2 py-1 rounded">data-theme</code> - "light" or "dark" (default: light)</li>
                <li><code className="bg-white px-2 py-1 rounded">data-genus</code> - Filter by specific genus (optional)</li>
                <li><code className="bg-white px-2 py-1 rounded">data-api-base-url</code> - Custom API endpoint (optional)</li>
              </ul>
            </div>
          </section>

          {/* API Documentation */}
          <section className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4">API Documentation</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-lg mb-2">Orchid Data Endpoint</h3>
                <code className="bg-gray-100 px-3 py-1 rounded">
                  GET /api/v2/orchids?limit=6&genus=Cattleya
                </code>
                <p className="text-gray-600 mt-2">
                  Returns orchid data in JSON format with photos, scientific names, and descriptions.
                </p>
              </div>
              
              <div>
                <h3 className="font-semibold text-lg mb-2">Database Statistics</h3>
                <code className="bg-gray-100 px-3 py-1 rounded">
                  GET /api/v2/stats
                </code>
                <p className="text-gray-600 mt-2">
                  Returns collection statistics including total orchids and photos available.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-lg mb-2">Individual Orchid</h3>
                <code className="bg-gray-100 px-3 py-1 rounded">
                  GET /api/v2/orchids/{id}
                </code>
                <p className="text-gray-600 mt-2">
                  Returns detailed information for a specific orchid including full AI descriptions.
                </p>
              </div>
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="text-center mt-12 py-8 border-t border-gray-200">
          <p className="text-gray-600">
            Built with ❤️ by the Five Cities Orchid Society | 
            <a href="mailto:support@fivecitiesorchids.org" className="text-blue-600 hover:underline ml-1">
              Contact Support
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default WidgetDemoPage;