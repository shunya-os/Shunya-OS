/**
 * Map View — OpenStreetMap + Leaflet
 *
 * Free, no API key needed. Displays locations on OpenStreetMap using Leaflet.
 * Features:
 * - Show address on map for contacts and customers
 * - Search for locations
 * - Add markers for stored addresses
 * - Warm glass-morphism design
 */
import { useState, useRef, useEffect, useCallback } from 'react';

// ── Types ──
interface MapLocation {
  lat: number;
  lng: number;
  label: string;
}

interface MapViewProps {
  address?: string;
  locations?: MapLocation[];
  onLocationSelect?: (loc: { lat: number; lng: number; label: string }) => void;
}

// ── Leaflet CDN ──
const LEAFLET_CSS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
const LEAFLET_JS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';

// ── Nominatim API (free, no key) ──
const NOMINATIM_SEARCH = 'https://nominatim.openstreetmap.org/search';

export function MapView({ address, locations = [], onLocationSelect }: MapViewProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const leafletLoadedRef = useRef(false);
  const leafletRef = useRef<any>(null);
  const [searchQuery, setSearchQuery] = useState(address || '');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [mapReady, setMapReady] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [cssLoaded, setCssLoaded] = useState(false);

  // Load Leaflet CSS
  useEffect(() => {
    if (document.querySelector('link[href="' + LEAFLET_CSS + '"]')) {
      setCssLoaded(true);
      return;
    }
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = LEAFLET_CSS;
    link.onload = () => setCssLoaded(true);
    document.head.appendChild(link);
    return () => {
      // don't remove on unmount — other instances may use it
    };
  }, []);

  // Load Leaflet JS and initialize map
  useEffect(() => {
    if (!cssLoaded || mapRef.current) return;

    const script = document.createElement('script');
    script.src = LEAFLET_JS;
    script.onload = () => {
      const L = (window as any).L;
      if (!L || !mapContainerRef.current) return;

      leafletRef.current = L;
      leafletLoadedRef.current = true;

      const map = L.map(mapContainerRef.current, {
        zoomControl: true,
        attributionControl: true,
      }).setView([20.5937, 78.9629], 5); // Default: India

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      mapRef.current = map;
      setMapReady(true);

      // If initial address provided, geocode it
      if (address) {
        geocodeAddress(address, map, L);
      }

      // If initial locations provided, add markers
      if (locations.length > 0) {
        addMarkersToMap(locations, map, L);
      }
    };
    document.body.appendChild(script);

    return () => {
      // Cleanup map on unmount
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cssLoaded]);

  // Geocode address
  const geocodeAddress = useCallback(
    async (addr: string, map?: any, L?: any) => {
      if (!addr.trim()) return;
      const L_ = L || leafletRef.current;
      const m = map || mapRef.current;
      if (!m || !L_) return;

      try {
        const res = await fetch(`${NOMINATIM_SEARCH}?q=${encodeURIComponent(addr)}&format=json&limit=5`);
        const data = await res.json();
        if (data && data.length > 0) {
          const result = data[0];
          const lat = parseFloat(result.lat);
          const lng = parseFloat(result.lon);
          m.setView([lat, lng], 14);
          setSearchResults(data);
          addMarker(lat, lng, result.display_name, m, L_);
          if (onLocationSelect) {
            onLocationSelect({ lat, lng, label: result.display_name });
          }
        }
      } catch {
        // silently fail — free API may be rate-limited
      }
    },
    [onLocationSelect],
  );

  // Add a single marker
  const addMarker = useCallback((lat: number, lng: number, label: string, map?: any, L?: any) => {
    const L_ = L || leafletRef.current;
    const m = map || mapRef.current;
    if (!m || !L_) return;

    const marker = L_.marker([lat, lng]).addTo(m);
    marker.bindPopup(
      `<div style="font-size:13px;font-family:system-ui,sans-serif;color:#1A1C1D;max-width:260px;">${label}</div>`,
    );
    markersRef.current.push(marker);
    return marker;
  }, []);

  // Add multiple markers
  const addMarkersToMap = useCallback(
    (locs: MapLocation[], map?: any, L?: any) => {
      const L_ = L || leafletRef.current;
      const m = map || mapRef.current;
      if (!m || !L_) return;

      locs.forEach((loc) => {
        addMarker(loc.lat, loc.lng, loc.label, m, L_);
      });

      // Fit bounds if multiple markers
      if (locs.length > 1) {
        const bounds = locs.map((l) => [l.lat, l.lng]);
        m.fitBounds(bounds, { padding: [50, 50] });
      }
    },
    [addMarker],
  );

  // Handle search
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    const L_ = leafletRef.current;
    const m = mapRef.current;

    try {
      const res = await fetch(`${NOMINATIM_SEARCH}?q=${encodeURIComponent(searchQuery)}&format=json&limit=5`);
      const data = await res.json();
      setSearchResults(data);
      if (data && data.length > 0 && m && L_) {
        const r = data[0];
        m.setView([parseFloat(r.lat), parseFloat(r.lon)], 14);
        // Clear existing markers
        markersRef.current.forEach((mkr) => m.removeLayer(mkr));
        markersRef.current = [];
        addMarker(parseFloat(r.lat), parseFloat(r.lon), r.display_name, m, L_);
      }
    } catch {
      // silently fail
    }
    setIsSearching(false);
  }, [searchQuery, addMarker]);

  // Handle result click
  const handleResultClick = useCallback(
    (result: any) => {
      const L_ = leafletRef.current;
      const m = mapRef.current;
      if (!m || !L_) return;
      const lat = parseFloat(result.lat);
      const lng = parseFloat(result.lon);
      m.setView([lat, lng], 14);
      markersRef.current.forEach((mkr) => m.removeLayer(mkr));
      markersRef.current = [];
      addMarker(lat, lng, result.display_name, m, L_);
      setSearchResults([]);
      setShowSearch(false);
      if (onLocationSelect) {
        onLocationSelect({ lat, lng, label: result.display_name });
      }
    },
    [addMarker, onLocationSelect],
  );

  // Initial geocode on address prop change
  useEffect(() => {
    if (address && mapReady) {
      setSearchQuery(address);
      geocodeAddress(address);
    }
  }, [address, mapReady, geocodeAddress]);

  // Initial locations on map ready
  useEffect(() => {
    if (locations.length > 0 && mapReady) {
      addMarkersToMap(locations);
    }
  }, [locations, mapReady, addMarkersToMap]);

  return (
    <div className="mv-container">
      {/* Toolbar */}
      <div className="mv-toolbar">
        <div className="mv-toolbar-left">
          <span className="mv-title">📍 Map View</span>
        </div>
        <div className="mv-toolbar-right">
          <button className="mv-btn mv-btn-ghost" onClick={() => setShowSearch(!showSearch)}>
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            Search
          </button>
        </div>
      </div>

      {/* Search Bar */}
      {showSearch && (
        <div className="mv-search-bar">
          <input
            className="mv-search-input"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSearch();
            }}
            placeholder="Search location..."
          />
          <button className="mv-btn mv-btn-primary" onClick={handleSearch} disabled={isSearching}>
            {isSearching ? '...' : 'Search'}
          </button>
        </div>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && showSearch && (
        <div className="mv-results">
          {searchResults.map((r: any, i: number) => (
            <button key={i} className="mv-result-item" onClick={() => handleResultClick(r)}>
              <span className="mv-result-name">{r.display_name}</span>
            </button>
          ))}
        </div>
      )}

      {/* Map */}
      <div className="mv-map-wrapper">
        <div ref={mapContainerRef} className="mv-map" style={{ height: '400px', width: '100%' }} />
        {!mapReady && (
          <div className="mv-loading">
            <div className="mv-loading-spinner" />
            <span>Loading map...</span>
          </div>
        )}
        {mapReady && locations.length === 0 && !address && (
          <div className="mv-hint">Search for a location or select a contact with an address.</div>
        )}
      </div>

      <style>{mvCss}</style>
    </div>
  );
}

// ── Styles ──
const mvCss = `
.mv-container {
  display: flex;
  flex-direction: column;
  gap: 0;
  width: 100%;
  box-sizing: border-box;
}

.mv-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(26,28,29,0.04);
  background: rgba(250,248,245,0.4);
}

.mv-toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mv-title {
  font-size: 13px;
  font-weight: 600;
  color: #1A1C1D;
}

.mv-toolbar-right {
  display: flex;
  gap: 6px;
}

.mv-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
  line-height: 1;
}

.mv-btn-ghost {
  background: transparent;
  color: rgba(26,28,29,0.45);
}
.mv-btn-ghost:hover {
  background: rgba(255,255,255,0.6);
  color: #1A1C1D;
}

.mv-btn-primary {
  background: linear-gradient(135deg, #6C4AE2, #A4865F);
  color: #fff;
  padding: 6px 14px;
}
.mv-btn-primary:hover {
  opacity: 0.9;
}
.mv-btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mv-search-bar {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(26,28,29,0.04);
  background: rgba(255,255,255,0.3);
}

.mv-search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid rgba(26,28,29,0.08);
  border-radius: 8px;
  background: rgba(255,255,255,0.7);
  font-size: 13px;
  font-family: inherit;
  color: #1A1C1D;
  outline: none;
}
.mv-search-input:focus {
  border-color: #6C4AE2;
}
.mv-search-input::placeholder {
  color: rgba(26,28,29,0.3);
}

.mv-results {
  display: flex;
  flex-direction: column;
  max-height: 180px;
  overflow-y: auto;
  border-bottom: 1px solid rgba(26,28,29,0.04);
}

.mv-result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border: none;
  background: rgba(255,255,255,0.5);
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  color: rgba(26,28,29,0.65);
  text-align: left;
  transition: all 0.1s;
  line-height: 1.4;
}
.mv-result-item:hover {
  background: rgba(108,74,226,0.06);
  color: #1A1C1D;
}
.mv-result-item:not(:last-child) {
  border-bottom: 1px solid rgba(26,28,29,0.03);
}

.mv-map-wrapper {
  position: relative;
  min-height: 400px;
}

.mv-map {
  border-radius: 0;
  z-index: 1;
}

.mv-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(250,248,245,0.8);
  color: rgba(26,28,29,0.45);
  font-size: 13px;
  z-index: 2;
}

.mv-loading-spinner {
  width: 28px;
  height: 28px;
  border: 2px solid rgba(108,74,226,0.15);
  border-top-color: #6C4AE2;
  border-radius: 50%;
  animation: mv-spin 0.8s linear infinite;
}

@keyframes mv-spin {
  to { transform: rotate(360deg); }
}

.mv-hint {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 16px;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(26,28,29,0.06);
  border-radius: 10px;
  font-size: 11px;
  color: rgba(26,28,29,0.45);
  white-space: nowrap;
  z-index: 3;
  pointer-events: none;
}

@media (max-width: 768px) {
  .mv-toolbar {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
  .mv-map {
    height: 300px !important;
  }
  .mv-map-wrapper {
    min-height: 300px;
  }
}
`;
