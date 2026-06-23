import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Hotspot } from '../services/api';

interface HotspotMapProps {
  hotspots: Hotspot[];
  selectedHotspot: Hotspot | null;
  onSelect: (hotspot: Hotspot) => void;
  onDeselect: () => void;
  theme?: 'dark' | 'light';
  visibleHotspotIds?: Set<string> | null;
}

const BENGALURU_CENTER: [number, number] = [77.5946, 12.9716];
const BENGALURU_ZOOM = 11.5;

const POINTS_SOURCE = 'hotspots-points';
const POLYGONS_SOURCE = 'hotspots-polygons';
const CIRCLES_LAYER = 'hotspots-circles';
const POLY_FILL_LAYER = 'hotspots-poly-fill';
const POLY_LINE_LAYER = 'hotspots-poly-line';

function styleUrl(theme: 'dark' | 'light') {
  return theme === 'light'
    ? 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json'
    : 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';
}

function getColors(theme: 'dark' | 'light') {
  return {
    low:      theme === 'light' ? '#16A34A' : '#10B981',
    medium:   theme === 'light' ? '#D97706' : '#F59E0B',
    high:     theme === 'light' ? '#EA580C' : '#F97316',
    critical: theme === 'light' ? '#DC2626' : '#EF4444',
    stroke:   theme === 'light' ? '#1e293b' : '#FFFFFF',
    teal:     '#5BC0BE',
  };
}

function severityColor(c: ReturnType<typeof getColors>): maplibregl.ExpressionSpecification {
  return [
    'case',
    ['==', ['get', 'selected'], 1],
    c.teal,
    ['step', ['get', 'impact_score'], c.low, 50, c.medium, 65, c.high, 80, c.critical]
  ];
}

function buildPointGeoJson(
  hotspots: Hotspot[],
  selectedId: string | null,
  visibleIds: Set<string> | null,
): GeoJSON.FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: hotspots.map((h) => {
      const isSelected = selectedId === h.id;
      const filteredOut = visibleIds !== null && !visibleIds.has(h.id);
      const dimmed = filteredOut || (selectedId !== null && !isSelected);
      return {
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [h.longitude, h.latitude] },
        properties: {
          hsid: h.id,
          name: h.name,
          violations: h.violations,
          impact_score: h.impact_score,
          dimmed: dimmed ? 1 : 0,
          selected: isSelected ? 1 : 0,
        },
      };
    }),
  };
}

function buildPolygonGeoJson(
  hotspots: Hotspot[],
  selectedId: string | null,
): GeoJSON.FeatureCollection {
  if (!selectedId) {
    return { type: 'FeatureCollection', features: [] };
  }

  const h = hotspots.find((x) => x.id === selectedId);
  if (!h?.polygon) {
    return { type: 'FeatureCollection', features: [] };
  }

  try {
    const parsed = JSON.parse(h.polygon);
    if (parsed?.type !== 'Polygon' || !Array.isArray(parsed.coordinates)) {
      return { type: 'FeatureCollection', features: [] };
    }

    return {
      type: 'FeatureCollection',
      features: [{
        type: 'Feature',
        geometry: parsed,
        properties: {
          hsid: h.id,
          name: h.name,
          violations: h.violations,
          impact_score: h.impact_score,
          selected: 1,
        },
      }],
    };
  } catch {
    return { type: 'FeatureCollection', features: [] };
  }
}

export const HotspotMap: React.FC<HotspotMapProps> = ({
  hotspots,
  selectedHotspot,
  onSelect,
  onDeselect,
  theme = 'dark',
  visibleHotspotIds = null,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const layersReadyRef = useRef(false);
  const hasFitBoundsRef = useRef(false);
  const skipThemeRef = useRef(true);
  const prevSelectedIdRef = useRef<string | null>(null);

  const hotspotsRef = useRef(hotspots);
  const selectedRef = useRef(selectedHotspot);
  const visibleRef = useRef(visibleHotspotIds);
  const themeRef = useRef(theme);
  const onSelectRef = useRef(onSelect);
  const onDeselectRef = useRef(onDeselect);

  hotspotsRef.current = hotspots;
  selectedRef.current = selectedHotspot;
  visibleRef.current = visibleHotspotIds;
  themeRef.current = theme;
  onSelectRef.current = onSelect;
  onDeselectRef.current = onDeselect;

  // Stable refs for functions used inside the one-time mount effect
  const installLayersRef = useRef<(map: maplibregl.Map) => void>(() => {});
  const pushDataRef = useRef<(map: maplibregl.Map) => void>(() => {});

  installLayersRef.current = (map: maplibregl.Map) => {
    const c = getColors(themeRef.current);
    const emptyPoints: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] };
    const emptyPolygons: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] };

    [POLY_LINE_LAYER, POLY_FILL_LAYER, CIRCLES_LAYER].forEach((id) => {
      if (map.getLayer(id)) map.removeLayer(id);
    });
    [POINTS_SOURCE, POLYGONS_SOURCE].forEach((id) => {
      if (map.getSource(id)) map.removeSource(id);
    });

    map.addSource(POINTS_SOURCE, { type: 'geojson', data: emptyPoints });
    map.addSource(POLYGONS_SOURCE, { type: 'geojson', data: emptyPolygons });

    map.addLayer({
      id: POLY_FILL_LAYER,
      type: 'fill',
      source: POLYGONS_SOURCE,
      paint: {
        'fill-color': severityColor(c),
        'fill-opacity': 0.35,
      },
    });

    map.addLayer({
      id: POLY_LINE_LAYER,
      type: 'line',
      source: POLYGONS_SOURCE,
      paint: {
        'line-color': severityColor(c),
        'line-width': 3,
        'line-opacity': 0.9,
      },
    });

    map.addLayer({
      id: CIRCLES_LAYER,
      type: 'circle',
      source: POINTS_SOURCE,
      paint: {
        'circle-radius': [
          'min',
          ['interpolate', ['linear'], ['get', 'violations'], 20, 8, 200, 14, 1000, 22],
          22,
        ],
        'circle-color': severityColor(c),
        'circle-opacity': ['case', ['==', ['get', 'dimmed'], 1], 0.25, 0.95],
        'circle-stroke-width': ['case', ['==', ['get', 'selected'], 1], 3, 1.5],
        'circle-stroke-color': ['case', ['==', ['get', 'selected'], 1], c.teal, c.stroke],
      },
    });

    layersReadyRef.current = true;
    pushDataRef.current(map);
  };

  pushDataRef.current = (map: maplibregl.Map) => {
    if (!layersReadyRef.current) return;

    const selectedId = selectedRef.current?.id ?? null;
    const visibleIds = visibleRef.current;
    const list = hotspotsRef.current;

    const pointsSrc = map.getSource(POINTS_SOURCE) as maplibregl.GeoJSONSource | undefined;
    const polySrc = map.getSource(POLYGONS_SOURCE) as maplibregl.GeoJSONSource | undefined;
    if (!pointsSrc || !polySrc) return;

    const pointsData = buildPointGeoJson(list, selectedId, visibleIds);
    pointsSrc.setData(pointsData);

    const polyData = buildPolygonGeoJson(list, selectedId);
    polySrc.setData(polyData);

    if (!hasFitBoundsRef.current && list.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      list.forEach((h) => bounds.extend([h.longitude, h.latitude]));
      if (!bounds.isEmpty()) {
        map.fitBounds(bounds, { padding: 48, maxZoom: 13, duration: 0 });
        hasFitBoundsRef.current = true;
      }
    }

    map.triggerRepaint();
  };

  // Create map once — empty deps, all dynamic state via refs
  useEffect(() => {
    if (!containerRef.current) return;

    layersReadyRef.current = false;
    hasFitBoundsRef.current = false;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleUrl(themeRef.current),
      center: BENGALURU_CENTER,
      zoom: BENGALURU_ZOOM,
      maxZoom: 17,
      minZoom: 9,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    const popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      className: 'custom-map-popup',
    });

    const attachInteractions = () => {
      map.off('mouseenter', CIRCLES_LAYER, onMouseEnter);
      map.off('mouseleave', CIRCLES_LAYER, onMouseLeave);
      map.off('click', CIRCLES_LAYER, onClickCircle);

      map.on('mouseenter', CIRCLES_LAYER, onMouseEnter);
      map.on('mouseleave', CIRCLES_LAYER, onMouseLeave);
      map.on('click', CIRCLES_LAYER, onClickCircle);
    };

    function onMouseEnter(e: maplibregl.MapMouseEvent & { features?: GeoJSON.Feature[] }) {
      map.getCanvas().style.cursor = 'pointer';
      const f = e.features?.[0];
      if (!f) return;
      const coords = (f.geometry as GeoJSON.Point).coordinates.slice() as [number, number];
      const { name, violations, impact_score } = f.properties as Record<string, string | number>;
      popup.setLngLat(coords).setHTML(`
        <div style="font-family:'Outfit',sans-serif;padding:6px;color:#1e293b;">
          <h4 style="font-weight:700;margin-bottom:4px;font-size:13px;">${name}</h4>
          <p style="margin:0;font-size:11px;">PII: <strong>${impact_score}</strong></p>
          <p style="margin:0;font-size:11px;">Violations: <strong>${violations}</strong></p>
        </div>`).addTo(map);
    }

    function onMouseLeave() {
      map.getCanvas().style.cursor = '';
      popup.remove();
    }

    function onClickCircle(e: maplibregl.MapMouseEvent & { features?: GeoJSON.Feature[] }) {
      const hsid = e.features?.[0]?.properties?.hsid as string | undefined;
      if (!hsid) return;
      const h = hotspotsRef.current.find((x) => x.id === hsid);
      if (!h) return;

      if (selectedRef.current?.id === h.id) {
        onDeselectRef.current();
      } else {
        onSelectRef.current(h);
      }
    }

    const setupLayers = () => {
      map.resize();
      installLayersRef.current(map);
      attachInteractions();
    };

    map.on('load', setupLayers);
    // setStyle (theme toggle) re-fires style.load but NOT load — must handle both
    map.on('style.load', setupLayers);

    const ro = new ResizeObserver(() => map.resize());
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      layersReadyRef.current = false;
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Push hotspot data whenever props change
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (map.loaded() && layersReadyRef.current) {
      pushDataRef.current(map);
      return;
    }

    const onReady = () => pushDataRef.current(map);
    map.once('load', onReady);
    return () => { map.off('load', onReady); };
  }, [hotspots, selectedHotspot, visibleHotspotIds]);

  // Theme toggle — skip the first render (map already created with correct style)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (skipThemeRef.current) {
      skipThemeRef.current = false;
      return;
    }
    layersReadyRef.current = false;
    map.setStyle(styleUrl(theme));
  }, [theme]);

  // Fly to selected hotspot (skip when deselected)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const currId = selectedHotspot?.id ?? null;
    const prevId = prevSelectedIdRef.current;
    prevSelectedIdRef.current = currId;

    if (selectedHotspot && currId !== prevId) {
      map.flyTo({
        center: [selectedHotspot.longitude, selectedHotspot.latitude],
        zoom: 14.5,
        speed: 1.2,
        curve: 1.42,
        essential: true,
      });
    }
  }, [selectedHotspot]);

  return (
    <div className="relative h-full min-h-[400px] w-full overflow-hidden rounded-xl border border-white/8 bg-[#070b16]">
      <div ref={containerRef} className="absolute inset-0 h-full w-full" />
      <div className="pointer-events-none absolute bottom-3 left-3 z-10 rounded-lg border border-white/8 bg-black/50 px-3 py-2 backdrop-blur-md">
        <div className="flex items-center gap-4 text-[11px] font-medium tracking-wide text-slate-300">
          {[
            { label: 'Critical', color: 'bg-severity-critical' },
            { label: 'High',     color: 'bg-severity-high'     },
            { label: 'Medium',   color: 'bg-severity-medium'   },
            { label: 'Low',      color: 'bg-severity-low'      },
          ].map((item) => (
            <span key={item.label} className="inline-flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${item.color} shadow-sm`} />
              {item.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
