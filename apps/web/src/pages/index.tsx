import { useState, useEffect } from 'react'
import Head from 'next/head'
import { Search, Sparkles, Globe, Microscope } from 'lucide-react'
import Layout from '../components/Layout'
import { OrchidCard } from '@orchid-continuum/ui'
import { fetchOrchids, fetchFeaturedOrchid } from '../lib/api'

interface Orchid {
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

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [featuredOrchids, setFeaturedOrchids] = useState<Orchid[]>([])
  const [orchidOfDay, setOrchidOfDay] = useState<Orchid | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      try {
        // Load featured orchids and orchid of the day
        const [orchidsResponse, featuredResponse] = await Promise.all([
          fetchOrchids({ limit: 6 }),
          fetchFeaturedOrchid()
        ])
        
        setFeaturedOrchids(orchidsResponse.data || [])
        setOrchidOfDay(featuredResponse.data)
      } catch (error) {
        console.error('Failed to load homepage data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      window.location.href = `/search?q=${encodeURIComponent(searchQuery)}`
    }
  }

  return (
    <Layout>
      <Head>
        <title>Orchid Continuum - Five Cities Orchid Society</title>
        <meta 
          name="description" 
          content="AI-enhanced orchid database and community platform for orchid enthusiasts, researchers, and growers." 
        />
      </Head>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white py-20">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-5xl font-bold mb-6">
            🌺 The Orchid Continuum
          </h1>
          <p className="text-xl mb-8 max-w-3xl mx-auto">
            Discover, identify, and cultivate orchids with AI-powered tools, 
            comprehensive care guides, and a global community of enthusiasts.
          </p>
          
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="max-w-md mx-auto mb-8">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search orchids..."
                className="w-full px-4 py-3 pl-12 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-400"
              />
              <Search className="absolute left-4 top-3.5 h-5 w-5 text-gray-400" />
              <button
                type="submit"
                className="absolute right-2 top-2 px-4 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
              >
                Search
              </button>
            </div>
          </form>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <a 
              href="/finder" 
              className="bg-white/10 backdrop-blur-sm rounded-lg p-6 hover:bg-white/20 transition-colors"
            >
              <Sparkles className="h-8 w-8 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Find by Conditions</h3>
              <p className="text-sm text-gray-200">
                Discover orchids perfect for your growing environment
              </p>
            </a>
            
            <a 
              href="/globe" 
              className="bg-white/10 backdrop-blur-sm rounded-lg p-6 hover:bg-white/20 transition-colors"
            >
              <Globe className="h-8 w-8 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">35th Parallel Globe</h3>
              <p className="text-sm text-gray-200">
                Explore orchid habitats around the world
              </p>
            </a>
            
            <a 
              href="/lab" 
              className="bg-white/10 backdrop-blur-sm rounded-lg p-6 hover:bg-white/20 transition-colors"
            >
              <Microscope className="h-8 w-8 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Science Lab</h3>
              <p className="text-sm text-gray-200">
                Advanced comparison and analysis tools
              </p>
            </a>
          </div>
        </div>
      </section>

      {/* Orchid of the Day */}
      {orchidOfDay && (
        <section className="py-16 bg-gray-50">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-8">🌟 Orchid of the Day</h2>
            <div className="max-w-2xl mx-auto">
              <OrchidCard 
                orchid={orchidOfDay}
                featured={true}
                className="shadow-lg"
              />
            </div>
          </div>
        </section>
      )}

      {/* Featured Orchids */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-8">Featured Orchids</h2>
          
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-gray-200 rounded-lg h-64 animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {featuredOrchids.map((orchid) => (
                <OrchidCard key={orchid.id} orchid={orchid} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Platform Features</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="bg-purple-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                🤖
              </div>
              <h3 className="font-semibold mb-2">AI Identification</h3>
              <p className="text-gray-600 text-sm">
                Upload photos for instant orchid identification using advanced AI
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                📊
              </div>
              <h3 className="font-semibold mb-2">Care Wheel</h3>
              <p className="text-gray-600 text-sm">
                Interactive care requirements with Baker culture data
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                🌍
              </div>
              <h3 className="font-semibold mb-2">GBIF Integration</h3>
              <p className="text-gray-600 text-sm">
                Access to global biodiversity occurrence data
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-yellow-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                📱
              </div>
              <h3 className="font-semibold mb-2">Embeddable Widgets</h3>
              <p className="text-gray-600 text-sm">
                Add orchid tools to any website with simple embed codes
              </p>
            </div>
          </div>
        </div>
      </section>
    </Layout>
  )
}