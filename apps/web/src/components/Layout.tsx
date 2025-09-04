import { ReactNode } from 'react'
import Link from 'next/link'
import { User, Menu, X } from 'lucide-react'
import { useState } from 'react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navigation = [
    { name: 'Home', href: '/' },
    { name: 'Search', href: '/search' },
    { name: 'Finder', href: '/finder' },
    { name: 'Gallery', href: '/gallery' },
    { name: 'Globe', href: '/globe' },
    { name: 'Science Lab', href: '/lab' },
  ]

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center space-x-2">
              <span className="text-2xl">🌺</span>
              <span className="font-bold text-xl text-gray-900">
                Orchid Continuum
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex space-x-8">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="text-gray-600 hover:text-purple-600 px-3 py-2 text-sm font-medium transition-colors"
                >
                  {item.name}
                </Link>
              ))}
            </div>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <button className="text-gray-600 hover:text-purple-600 transition-colors">
                <User className="h-5 w-5" />
              </button>
              
              {/* Mobile Menu Button */}
              <button
                className="md:hidden text-gray-600 hover:text-purple-600"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? (
                  <X className="h-6 w-6" />
                ) : (
                  <Menu className="h-6 w-6" />
                )}
              </button>
            </div>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="md:hidden border-t border-gray-200 py-4">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="block px-3 py-2 text-gray-600 hover:text-purple-600 font-medium"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {item.name}
                </Link>
              ))}
            </div>
          )}
        </div>
      </nav>

      {/* Main Content */}
      <main>{children}</main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <span className="text-2xl">🌺</span>
                <span className="font-bold text-lg">Orchid Continuum</span>
              </div>
              <p className="text-gray-400 text-sm">
                AI-enhanced orchid database for the Five Cities Orchid Society
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Tools</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><Link href="/finder" className="hover:text-white">Orchid Finder</Link></li>
                <li><Link href="/identify" className="hover:text-white">AI Identification</Link></li>
                <li><Link href="/care-wheel" className="hover:text-white">Care Wheel</Link></li>
                <li><Link href="/compare" className="hover:text-white">Comparison Tool</Link></li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Explore</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><Link href="/gallery" className="hover:text-white">Photo Gallery</Link></li>
                <li><Link href="/globe" className="hover:text-white">35th Parallel Globe</Link></li>
                <li><Link href="/lab" className="hover:text-white">Science Lab</Link></li>
                <li><Link href="/mahjong" className="hover:text-white">Mahjong Game</Link></li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Community</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><Link href="/collections" className="hover:text-white">My Collection</Link></li>
                <li><Link href="/contests" className="hover:text-white">Photo Contests</Link></li>
                <li><Link href="/help" className="hover:text-white">Help & Support</Link></li>
                <li><Link href="/embed" className="hover:text-white">Embed Widgets</Link></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
            <p>&copy; 2025 Five Cities Orchid Society. Powered by The Orchid Continuum.</p>
            <p className="mt-2">
              Data sources: GBIF, Baker Culture Sheets, AOS Guidelines, Google Drive Collections
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}