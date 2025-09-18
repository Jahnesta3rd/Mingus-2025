import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Clock, DollarSign, Car, Bus, Bike, AlertCircle, Loader2 } from 'lucide-react';
import { useAnalytics } from '../hooks/useAnalytics';

interface JobLocation {
  id: string;
  title: string;
  company: string;
  latitude: number;
  longitude: number;
  distance_miles: number;
  salary_range: string;
  tier: 'conservative' | 'optimal' | 'stretch';
  commute_options: {
    driving: { time_minutes: number; cost_monthly: number };
    transit: { time_minutes: number; cost_monthly: number };
    walking: { time_minutes: number; cost_monthly: number };
  };
}

interface MapState {
  userLocation: { lat: number; lng: number };
  selectedRadius: number;
  jobs: JobLocation[];
  selectedJob: JobLocation | null;
  commuteMode: 'driving' | 'transit' | 'walking';
  showSalaryHeatmap: boolean;
}

interface LocationIntelligenceMapProps {
  className?: string;
}

const LocationIntelligenceMap: React.FC<LocationIntelligenceMapProps> = ({ className = '' }) => {
  const { trackInteraction, trackError } = useAnalytics();
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const directionsRendererRef = useRef<any>(null);
  
  const [mapState, setMapState] = useState<MapState>({
    userLocation: { lat: 0, lng: 0 },
    selectedRadius: 10,
    jobs: [],
    selectedJob: null,
    commuteMode: 'driving',
    showSalaryHeatmap: false
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize map and user location
  useEffect(() => {
    initializeMap();
    getUserLocation();
  }, []);

  // Update jobs when radius or location changes
  useEffect(() => {
    if (mapState.userLocation.lat !== 0 && mapLoaded) {
      fetchJobsInRadius();
    }
  }, [mapState.selectedRadius, mapState.userLocation, mapLoaded]);

  const initializeMap = useCallback(async () => {
    if (!mapRef.current) return;

    try {
      // Check if Google Maps is loaded
      if (typeof window.google === 'undefined') {
        // Load Google Maps script if not already loaded
        await loadGoogleMapsScript();
      }

      const map = new window.google.maps.Map(mapRef.current, {
        zoom: 10,
        center: { lat: 37.7749, lng: -122.4194 }, // Default to San Francisco
        styles: [
          {
            featureType: 'poi.business',
            stylers: [{ visibility: 'off' }]
          },
          {
            featureType: 'transit',
            elementType: 'labels',
            stylers: [{ visibility: 'off' }]
          }
        ],
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true,
        zoomControl: true
      });

      mapInstanceRef.current = map;
      setMapLoaded(true);

      // Track map initialization
      await trackInteraction('location_map_initialized', {
        map_type: 'google_maps',
        user_agent: navigator.userAgent
      });

    } catch (err) {
      console.error('Map initialization failed:', err);
      setError('Failed to initialize map. Please refresh the page.');
      await trackError(err as Error, { context: 'map_initialization' });
    }
  }, [trackInteraction, trackError]);

  const loadGoogleMapsScript = (): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (window.google && window.google.maps) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${process.env.REACT_APP_GOOGLE_MAPS_API_KEY || 'YOUR_API_KEY'}&libraries=places`;
      script.async = true;
      script.defer = true;
      
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Google Maps'));
      
      document.head.appendChild(script);
    });
  };

  const getUserLocation = useCallback(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const userLoc = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          
          setMapState(prev => ({ ...prev, userLocation: userLoc }));
          
          if (mapInstanceRef.current) {
            mapInstanceRef.current.setCenter(userLoc);
            addUserLocationMarker(userLoc);
          }

          await trackInteraction('user_location_detected', {
            location_type: 'coordinates',
            accuracy: position.coords.accuracy
          });
        },
        async (error) => {
          console.error('Geolocation error:', error);
          // Fallback to zipcode-based location
          await getLocationFromZipcode();
          await trackError(new Error(`Geolocation error: ${error.message}`), { context: 'geolocation_fallback' });
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000
        }
      );
    } else {
      getLocationFromZipcode();
    }
  }, [trackInteraction, trackError]);

  const getLocationFromZipcode = async () => {
    try {
      const response = await fetch('/api/location/geocode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zipcode: getUserLocationFromStorage() })
      });

      if (response.ok) {
        const data = await response.json();
        const userLoc = { lat: data.latitude, lng: data.longitude };
        setMapState(prev => ({ ...prev, userLocation: userLoc }));
        
        if (mapInstanceRef.current) {
          mapInstanceRef.current.setCenter(userLoc);
          addUserLocationMarker(userLoc);
        }
      }
    } catch (err) {
      console.error('Failed to get location from zipcode:', err);
    }
  };

  const fetchJobsInRadius = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/risk/jobs-in-radius', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-CSRF-Token': getCSRFToken()
        },
        body: JSON.stringify({
          user_location: mapState.userLocation,
          radius_miles: mapState.selectedRadius,
          include_commute_data: true
        })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch jobs in radius');
      }

      const data = await response.json();
      
      setMapState(prev => ({ ...prev, jobs: data.jobs || [] }));
      
      // Update map markers
      updateMapMarkers(data.jobs || []);
      
      // Update radius circle
      updateRadiusCircle(mapState.userLocation, mapState.selectedRadius);
      
      // Track analytics
      await trackInteraction('location_map_jobs_loaded', {
        radius: mapState.selectedRadius,
        jobs_found: data.jobs?.length || 0,
        user_location_type: 'coordinates'
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load job data';
      setError(errorMessage);
      console.error('Failed to fetch jobs in radius:', err);
      await trackError(err as Error, { context: 'jobs_fetch' });
    } finally {
      setLoading(false);
    }
  }, [mapState.userLocation, mapState.selectedRadius, trackInteraction, trackError]);

  const handleRadiusChange = useCallback(async (newRadius: number) => {
    setMapState(prev => ({ ...prev, selectedRadius: newRadius }));
    
    // Track radius change
    await trackInteraction('location_radius_changed', {
      previous_radius: mapState.selectedRadius,
      new_radius: newRadius,
      jobs_in_previous_radius: mapState.jobs.length
    });
  }, [mapState.selectedRadius, mapState.jobs.length, trackInteraction]);

  const handleJobMarkerClick = useCallback(async (job: JobLocation) => {
    setMapState(prev => ({ ...prev, selectedJob: job }));
    
    // Center map on selected job
    if (mapInstanceRef.current) {
      mapInstanceRef.current.panTo({ lat: job.latitude, lng: job.longitude });
    }
    
    // Show commute route
    displayCommuteRoute(mapState.userLocation, {
      lat: job.latitude,
      lng: job.longitude
    }, mapState.commuteMode);
    
    // Track job selection
    await trackInteraction('map_job_selected', {
      job_id: job.id,
      company: job.company,
      distance_miles: job.distance_miles,
      tier: job.tier
    });
  }, [mapState.userLocation, mapState.commuteMode, trackInteraction]);

  const updateMapMarkers = useCallback((jobs: JobLocation[]) => {
    if (!mapInstanceRef.current) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.setMap(null));
    markersRef.current = [];

    // Add new markers for each job with tier-based styling
    jobs.forEach(job => {
      const marker = new window.google.maps.Marker({
        position: { lat: job.latitude, lng: job.longitude },
        map: mapInstanceRef.current,
        title: `${job.title} at ${job.company}`,
        icon: getMarkerIcon(job.tier),
        zIndex: job.tier === 'optimal' ? 1000 : 100
      });
      
      marker.addListener('click', () => handleJobMarkerClick(job));
      markersRef.current.push(marker);
    });
  }, [handleJobMarkerClick]);

  const getMarkerIcon = useCallback((tier: string) => {
    const colors = {
      conservative: '#2563eb', // Blue
      optimal: '#7c3aed',      // Purple  
      stretch: '#ea580c'       // Orange
    };
    
    return {
      url: `data:image/svg+xml,${encodeURIComponent(`
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="16" cy="16" r="12" fill="${colors[tier as keyof typeof colors]}" stroke="white" stroke-width="2"/>
          <circle cx="16" cy="16" r="4" fill="white"/>
        </svg>
      `)}`,
      scaledSize: new window.google.maps.Size(32, 32),
      anchor: new window.google.maps.Point(16, 16)
    };
  }, []);

  const addUserLocationMarker = useCallback((location: { lat: number; lng: number }) => {
    if (!mapInstanceRef.current) return;

    new window.google.maps.Marker({
      position: location,
      map: mapInstanceRef.current,
      title: 'Your Location',
      icon: {
        url: `data:image/svg+xml,${encodeURIComponent(`
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" fill="#3b82f6" stroke="white" stroke-width="2"/>
            <circle cx="12" cy="12" r="4" fill="white"/>
          </svg>
        `)}`,
        scaledSize: new window.google.maps.Size(24, 24),
        anchor: new window.google.maps.Point(12, 12)
      }
    });
  }, []);

  const updateRadiusCircle = useCallback((center: { lat: number; lng: number }, radius: number) => {
    if (!mapInstanceRef.current) return;

    // Remove existing circle
    if (window.radiusCircle) {
      window.radiusCircle.setMap(null);
    }

    // Add new circle
    window.radiusCircle = new window.google.maps.Circle({
      strokeColor: '#3b82f6',
      strokeOpacity: 0.8,
      strokeWeight: 2,
      fillColor: '#3b82f6',
      fillOpacity: 0.1,
      map: mapInstanceRef.current,
      center: center,
      radius: radius * 1609.34 // Convert miles to meters
    });
  }, []);

  const displayCommuteRoute = useCallback((origin: any, destination: any, mode: string) => {
    if (!mapInstanceRef.current) return;

    const directionsService = new window.google.maps.DirectionsService();
    const directionsRenderer = new window.google.maps.DirectionsRenderer({
      suppressMarkers: true,
      polylineOptions: {
        strokeColor: '#7c3aed',
        strokeWeight: 4,
        strokeOpacity: 0.8
      }
    });
    
    directionsRenderer.setMap(mapInstanceRef.current);
    directionsRendererRef.current = directionsRenderer;
    
    const travelModeMap = {
      driving: window.google.maps.TravelMode.DRIVING,
      transit: window.google.maps.TravelMode.TRANSIT,
      walking: window.google.maps.TravelMode.WALKING
    };
    
    const travelMode = travelModeMap[mode as keyof typeof travelModeMap];
    
    directionsService.route({
      origin: origin,
      destination: destination,
      travelMode: travelMode
    }, (result: any, status: any) => {
      if (status === 'OK' && result) {
        directionsRenderer.setDirections(result);
      }
    });
  }, []);


  if (loading && !mapLoaded) {
    return <LocationMapSkeleton />;
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-xl p-8 text-center ${className}`}>
        <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-red-900 mb-2">Map Unavailable</h3>
        <p className="text-red-700 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
        >
          Refresh Page
        </button>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-lg overflow-hidden ${className}`}>
      {/* Map Controls Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Job Opportunities Map</h3>
            <p className="text-sm text-gray-600">
              {mapState.jobs.length} opportunities within {mapState.selectedRadius} miles
            </p>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {/* Radius Selector */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">Radius:</label>
              <select
                value={mapState.selectedRadius}
                onChange={(e) => handleRadiusChange(Number(e.target.value))}
                className="border border-gray-300 rounded-md px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={loading}
              >
                <option value={5}>5 miles</option>
                <option value={10}>10 miles</option>
                <option value={30}>30 miles</option>
                <option value={999}>Nationwide</option>
              </select>
            </div>
            
            {/* View Options */}
            <div className="flex border border-gray-300 rounded-md overflow-hidden">
              <button
                onClick={() => setMapState(prev => ({ ...prev, showSalaryHeatmap: false }))}
                className={`px-3 py-1 text-sm transition-colors ${
                  !mapState.showSalaryHeatmap 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Jobs
              </button>
              <button
                onClick={() => setMapState(prev => ({ ...prev, showSalaryHeatmap: true }))}
                className={`px-3 py-1 text-sm transition-colors ${
                  mapState.showSalaryHeatmap 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                Salary Heat
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Map Container */}
      <div className="relative h-96 lg:h-[500px]">
        <div ref={mapRef} className="w-full h-full" />
        
        {/* Loading Overlay */}
        {loading && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
            <div className="text-center">
              <Loader2 className="h-8 w-8 text-blue-600 animate-spin mx-auto mb-2" />
              <p className="text-sm text-gray-600">Loading opportunities...</p>
            </div>
          </div>
        )}
        
        {/* Tier Legend */}
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-md p-3">
          <div className="text-xs font-semibold text-gray-700 mb-2">Job Tiers</div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-600"></div>
              <span className="text-xs text-gray-600">Conservative</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-purple-600"></div>
              <span className="text-xs text-gray-600">Optimal</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-orange-600"></div>
              <span className="text-xs text-gray-600">Stretch</span>
            </div>
          </div>
        </div>

        {/* Commute Mode Selector */}
        <div className="absolute top-4 right-4 bg-white rounded-lg shadow-md p-2">
          <div className="flex gap-1">
            {[
              { mode: 'driving', icon: Car, label: 'Drive' },
              { mode: 'transit', icon: Bus, label: 'Transit' },
              { mode: 'walking', icon: Bike, label: 'Bike/Walk' }
            ].map(({ mode, icon: Icon, label }) => (
              <button
                key={mode}
                onClick={() => setMapState(prev => ({ ...prev, commuteMode: mode as any }))}
                className={`p-2 rounded text-xs transition-colors ${
                  mapState.commuteMode === mode 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
                title={label}
              >
                <Icon className="h-4 w-4" />
              </button>
            ))}
          </div>
        </div>
      </div>
      
      {/* Selected Job Details Panel */}
      {mapState.selectedJob && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <JobLocationDetails
            job={mapState.selectedJob}
            commuteMode={mapState.commuteMode}
            onCommuteModeChange={(mode) => setMapState(prev => ({ ...prev, commuteMode: mode }))}
            onClose={() => setMapState(prev => ({ ...prev, selectedJob: null }))}
          />
        </div>
      )}
    </div>
  );
};

// Job Location Details Component
const JobLocationDetails: React.FC<{
  job: JobLocation;
  commuteMode: string;
  onCommuteModeChange: (mode: 'driving' | 'transit' | 'walking') => void;
  onClose: () => void;
}> = ({ job, commuteMode, onCommuteModeChange, onClose }) => {
  
  const currentCommute = job.commute_options[commuteMode as keyof typeof job.commute_options];
  
  return (
    <div className="bg-white rounded-lg p-4 shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-semibold text-gray-900">{job.title}</h4>
          <p className="text-sm text-gray-600">{job.company}</p>
          <p className="text-xs text-gray-500">{job.distance_miles.toFixed(1)} miles away</p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close job details"
        >
          ✕
        </button>
      </div>
      
      {/* Commute Options */}
      <div className="mb-3">
        <div className="text-sm font-medium text-gray-700 mb-2">Commute Options</div>
        <div className="flex gap-2">
          {[
            { mode: 'driving', icon: Car, label: 'Drive' },
            { mode: 'transit', icon: Bus, label: 'Transit' },
            { mode: 'walking', icon: Bike, label: 'Bike/Walk' }
          ].map(({ mode, icon: Icon, label }) => (
            <button
              key={mode}
              onClick={() => onCommuteModeChange(mode as any)}
              className={`
                flex items-center gap-1 px-3 py-2 rounded-md text-xs font-medium transition-colors
                ${commuteMode === mode 
                  ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }
              `}
            >
              <Icon className="h-3 w-3" />
              {label}
            </button>
          ))}
        </div>
      </div>
      
      {/* Commute Details */}
      <div className="grid grid-cols-2 gap-4 text-sm mb-3">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-gray-400" />
          <span>{currentCommute.time_minutes} min</span>
        </div>
        <div className="flex items-center gap-2">
          <DollarSign className="h-4 w-4 text-gray-400" />
          <span>${currentCommute.cost_monthly}/mo</span>
        </div>
      </div>

      {/* Salary Range */}
      <div className="mb-3">
        <div className="text-sm font-medium text-gray-700 mb-1">Salary Range</div>
        <div className="text-lg font-semibold text-gray-900">{job.salary_range}</div>
      </div>
      
      {/* Action Buttons */}
      <div className="flex gap-2">
        <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-md transition-colors">
          View Details
        </button>
        <button className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium py-2 rounded-md transition-colors">
          Save Job
        </button>
      </div>
    </div>
  );
};

// Loading Skeleton
const LocationMapSkeleton: React.FC = () => {
  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      <div className="p-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <div className="h-6 w-48 bg-gray-200 rounded animate-pulse mb-2" />
            <div className="h-4 w-64 bg-gray-200 rounded animate-pulse" />
          </div>
          <div className="flex gap-2">
            <div className="h-8 w-20 bg-gray-200 rounded animate-pulse" />
            <div className="h-8 w-16 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
      </div>
      
      <div className="relative h-96 lg:h-[500px] bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-2" />
          <p className="text-sm text-gray-500">Initializing map...</p>
        </div>
      </div>
    </div>
  );
};

// Helper Functions
const getUserLocationFromStorage = (): string => {
  return localStorage.getItem('user_location') || 'United States';
};

const getCSRFToken = (): string => {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    return metaTag.getAttribute('content') || '';
  }
  
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrf_token') {
      return value;
    }
  }
  
  return '';
};

// Extend window interface for Google Maps
declare global {
  interface Window {
    google: any;
    radiusCircle: any;
  }
}

export default LocationIntelligenceMap;
