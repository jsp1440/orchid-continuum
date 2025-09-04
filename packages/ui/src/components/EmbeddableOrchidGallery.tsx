import React, { useEffect, useState } from 'react';

interface Orchid {
  id: number;
  scientific_name: string;
  genus: string;
  species: string;
  description: string;
  photo_url: string | null;
  drive_id: string | null;
}

interface OrchidGalleryProps {
  apiBaseUrl?: string;
  limit?: number;
  genus?: string;
  theme?: 'light' | 'dark';
  style?: React.CSSProperties;
}

export const EmbeddableOrchidGallery: React.FC<OrchidGalleryProps> = ({
  apiBaseUrl = 'https://your-replit-domain.replit.app',
  limit = 6,
  genus,
  theme = 'light',
  style = {}
}) => {
  const [orchids, setOrchids] = useState<Orchid[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrchids = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams({
          limit: limit.toString(),
          ...(genus && { genus })
        });
        
        const response = await fetch(`${apiBaseUrl}/api/v2/orchids?${params}`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        setOrchids(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch orchids:', err);
        setError('Failed to load orchid data. Please check the API connection.');
      } finally {
        setLoading(false);
      }
    };

    fetchOrchids();
  }, [apiBaseUrl, limit, genus]);

  const themeClasses = theme === 'dark' 
    ? 'bg-gray-900 text-white' 
    : 'bg-white text-gray-900';

  if (loading) {
    return (
      <div className={`p-6 rounded-lg shadow-lg ${themeClasses}`} style={style}>
        <div className="animate-pulse">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: limit }).map((_, i) => (
              <div key={i} className="bg-gray-200 rounded-lg h-64 animate-pulse"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-6 rounded-lg shadow-lg ${themeClasses}`} style={style}>
        <div className="text-center py-8">
          <div className="text-red-500 mb-2">🌺</div>
          <h3 className="text-lg font-semibold mb-2">Connection Error</h3>
          <p className="text-sm opacity-70">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-6 rounded-lg shadow-lg ${themeClasses}`} style={style}>
      <div className="mb-6 text-center">
        <h2 className="text-2xl font-bold mb-2">
          🌺 Five Cities Orchid Society Collection
        </h2>
        <p className="opacity-70">
          {genus ? `${genus} species` : 'Featured orchids'} from our digital collection
        </p>
      </div>

      {orchids.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-4xl mb-4">🔍</div>
          <h3 className="text-lg font-semibold mb-2">No orchids found</h3>
          <p className="text-sm opacity-70">
            Try adjusting your search criteria or check back later.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {orchids.map((orchid) => (
            <div
              key={orchid.id}
              className={`rounded-lg overflow-hidden shadow-md transition-transform hover:scale-105 ${
                theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50'
              }`}
            >
              <div className="aspect-w-4 aspect-h-3">
                {orchid.photo_url ? (
                  <img
                    src={orchid.photo_url}
                    alt={orchid.scientific_name}
                    className="w-full h-48 object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzlmYTJhOCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPvCfjLo8L3RleHQ+PC9zdmc+';
                    }}
                  />
                ) : (
                  <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
                    <span className="text-4xl">🌺</span>
                  </div>
                )}
              </div>
              
              <div className="p-4">
                <h3 className="font-semibold text-sm mb-1 italic">
                  {orchid.scientific_name || 'Unknown species'}
                </h3>
                <p className="text-xs opacity-70 mb-2">
                  {orchid.genus && orchid.species 
                    ? `${orchid.genus} ${orchid.species}`
                    : orchid.genus || 'Unknown genus'
                  }
                </p>
                {orchid.description && (
                  <p className="text-xs opacity-60 line-clamp-3">
                    {orchid.description.substring(0, 100)}
                    {orchid.description.length > 100 ? '...' : ''}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 text-center">
        <a
          href={`${apiBaseUrl}/gallery`}
          target="_blank"
          rel="noopener noreferrer"
          className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            theme === 'dark'
              ? 'bg-purple-600 hover:bg-purple-700 text-white'
              : 'bg-purple-600 hover:bg-purple-700 text-white'
          }`}
        >
          View Full Collection →
        </a>
      </div>
    </div>
  );
};

export default EmbeddableOrchidGallery;