// GBIF API utilities and types

export interface GBIFOccurrence {
  key: number
  datasetKey: string
  publishingOrgKey: string
  scientificName: string
  kingdom?: string
  phylum?: string
  class?: string
  order?: string
  family?: string
  genus?: string
  species?: string
  decimalLatitude?: number
  decimalLongitude?: number
  elevation?: number
  country?: string
  stateProvince?: string
  locality?: string
  eventDate?: string
  basisOfRecord: string
  issues?: string[]
}

export interface GBIFSpecies {
  key: number
  scientificName: string
  canonicalName?: string
  authorship?: string
  nameType: string
  rank: string
  status: string
  confidence?: number
  synonym?: boolean
  class?: string
  family?: string
  genus?: string
  kingdom?: string
  order?: string
  phylum?: string
  species?: string
}

export interface GBIFMedia {
  key: number
  type: string
  format?: string
  identifier: string
  references?: string
  title?: string
  description?: string
  created?: string
  creator?: string
  contributor?: string
  publisher?: string
  audience?: string
  source?: string
  license?: string
  rightsHolder?: string
}

export class GBIFClient {
  private baseUrl = 'https://api.gbif.org/v1'

  async searchSpecies(name: string): Promise<GBIFSpecies[]> {
    const response = await fetch(
      `${this.baseUrl}/species/search?q=${encodeURIComponent(name)}&limit=10`
    )
    const data = await response.json()
    return data.results || []
  }

  async matchSpecies(name: string): Promise<GBIFSpecies | null> {
    const response = await fetch(
      `${this.baseUrl}/species/match?name=${encodeURIComponent(name)}`
    )
    const data = await response.json()
    return data.usageKey ? data : null
  }

  async getOccurrences(taxonKey: number, options: {
    hasCoordinate?: boolean
    limit?: number
    offset?: number
    country?: string
  } = {}): Promise<{ results: GBIFOccurrence[], count: number }> {
    const params = new URLSearchParams({
      taxonKey: taxonKey.toString(),
      limit: (options.limit || 20).toString(),
      offset: (options.offset || 0).toString(),
    })

    if (options.hasCoordinate) {
      params.append('hasCoordinate', 'true')
    }

    if (options.country) {
      params.append('country', options.country)
    }

    const response = await fetch(
      `${this.baseUrl}/occurrence/search?${params}`
    )
    const data = await response.json()
    
    return {
      results: data.results || [],
      count: data.count || 0
    }
  }

  async getSpeciesMedia(taxonKey: number): Promise<GBIFMedia[]> {
    const response = await fetch(
      `${this.baseUrl}/species/${taxonKey}/media`
    )
    const data = await response.json()
    return data.results || []
  }

  async getOccurrenceMedia(occurrenceKey: number): Promise<GBIFMedia[]> {
    const response = await fetch(
      `${this.baseUrl}/occurrence/${occurrenceKey}/media`
    )
    const data = await response.json()
    return data.results || []
  }

  // Utility function to extract orchid families
  isOrchidFamily(family?: string): boolean {
    return family?.toLowerCase() === 'orchidaceae'
  }

  // Format scientific name consistently
  formatScientificName(species: GBIFSpecies): string {
    if (species.canonicalName) {
      return species.canonicalName
    }
    return species.scientificName
  }

  // Generate citation for GBIF data
  generateCitation(occurrence: GBIFOccurrence): string {
    const year = new Date().getFullYear()
    return `GBIF.org (${year}). GBIF Occurrence Download. https://doi.org/10.15468/dl.${occurrence.key}`
  }
}

export const gbifClient = new GBIFClient()