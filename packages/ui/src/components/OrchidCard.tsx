import React from 'react'
import { Heart, Star, MapPin } from 'lucide-react'
import { clsx } from 'clsx'

interface OrchidCardProps {
  orchid: {
    id: string
    scientific_name: string
    genus: string
    species?: string
    description?: string
    primary_photo?: {
      url: string
      credited_to?: string
    }
  }
  featured?: boolean
  className?: string
  onClick?: () => void
}

export function OrchidCard({ orchid, featured = false, className, onClick }: OrchidCardProps) {
  const handleClick = () => {
    if (onClick) {
      onClick()
    } else {
      window.location.href = `/orchids/${orchid.id}`
    }
  }

  return (
    <div 
      className={clsx(
        'bg-white rounded-lg shadow-md overflow-hidden transition-all duration-200 hover:shadow-lg hover:-translate-y-1 cursor-pointer',
        featured && 'ring-2 ring-purple-400',
        className
      )}
      onClick={handleClick}
    >
      {/* Image */}
      <div className="relative h-48 bg-gray-200">
        {orchid.primary_photo?.url ? (
          <img
            src={orchid.primary_photo.url}
            alt={orchid.scientific_name}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <span className="text-4xl">🌺</span>
          </div>
        )}
        
        {featured && (
          <div className="absolute top-2 left-2">
            <Star className="h-5 w-5 text-yellow-400 fill-current" />
          </div>
        )}
        
        <button className="absolute top-2 right-2 p-1 bg-white/80 rounded-full hover:bg-white transition-colors">
          <Heart className="h-4 w-4 text-gray-600 hover:text-red-500" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="font-semibold text-lg text-gray-900 mb-1">
          <em>{orchid.scientific_name}</em>
        </h3>
        
        <div className="flex items-center text-sm text-gray-600 mb-2">
          <MapPin className="h-3 w-3 mr-1" />
          <span>Genus: {orchid.genus}</span>
        </div>
        
        {orchid.description && (
          <p className="text-sm text-gray-600 line-clamp-2 mb-3">
            {orchid.description}
          </p>
        )}
        
        {orchid.primary_photo?.credited_to && (
          <p className="text-xs text-gray-400">
            Photo: {orchid.primary_photo.credited_to}
          </p>
        )}
      </div>
    </div>
  )
}