import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Hotspot, Prediction } from '../services/api';

interface HotspotMapProps {
  hotspots: Hotspot[];
  selectedHotspot: Hotspot | null;
  predictions: Prediction[];
  onSelect: (hotspot: Hotspot) => void;
  onDeselect: () => void;
  visibleHotspotIds?: Set<string> | null;
  colorBy?: 'pii' | 'risk';
  piiThresholds?: { critical: number; high: number; medium: number };
}

const BENGALURU_CENTER: [number, number] = [77.5946, 12.9716];
const BENGALURU_ZOOM = 11.5;

const POINTS_SOURCE = 'hotspots-points';
const POLYGONS_SOURCE = 'hotspots-polygons';
const CIRCLES_LAYER = 'hotspots-circles';
const POLY_FILL_LAYER = 'hotspots-poly-fill';
const POLY_LINE_LAYER = 'hotspots-poly-line';

const DARK_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

const COLORS = {
  low: '#10B981',
  medium: '#F59E0B',
  high: '#F97316',
  critical: '#EF4444',
  stroke: '#FFFFFF',
  teal: '#5BC0BE',
} as const;

function severityColor(
  field: string,
  thresholds?: { critical: number; high: number; medium: number },
): maplibregl.ExpressionSpecification {
  if (field === 'risk_level') {
    return [
      'case',
      ['==', ['get', 'risk_level'], 'Critical'], COLORS.critical,
      ['==', ['get', 'risk_level'], 'High'], COLORS.high,
      ['==', ['get', 'risk_level'], 'Medium'], COLORS.medium,
      COLORS.low,
    ];
  }
  const t = thresholds ?? { critical: 60, high: 55, medium: 49 };
  return ['step', ['get', 'impact_score'], COLORS.low, t.medium, COLORS.medium, t.high, COLORS.high, t.critical, COLORS.critical];
}

function buildPointGeoJson(
  hotspots: Hotspot[],
  selectedId: string | null,
  visibleIds: Set<string> | null,
  colorBy: 'pii' | 'risk',
  predictions: Prediction[],
): GeoJSON.FeatureCollection {
  const list = visibleIds !== null ? hotspots.filter((h) => visibleIds.has(h.id)) : hotspots;
  return {
    type: 'FeatureCollection',
    features: list.map((h) => {
      const isSelected = selectedId === h.id;
      const dimmed = selectedId !== null && !isSelected;
      const pred = predictions.find((p) => p.hotspot_id === h.id);
      return {
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [h.longitude, h.latitude] },
        properties: {
          hsid: h.id,
          name: h.name,
          violations: h.violations,
          impact_score: h.impact_score,
          risk_level: colorBy === 'risk' ? (pred?.risk_level ?? 'Low') : '',
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
      features: [
        {
          type: 'Feature',
          geometry: parsed,
          properties: {
            hsid: h.id,
            name: h.name,
            violations: h.violations,
            impact_score: h.impact_score,
            selected: 1,
          },
        },
      ],
    };
  } catch {
    return { type: 'FeatureCollection', features: [] };
  }
}

export const HotspotMap: React.FC<HotspotMapProps> = ({
  hotspots,
  selectedHotspot,
  predictions,
  onSelect,
  onDeselect,
  visibleHotspotIds = null,
  colorBy = 'pii',
  piiThresholds,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const layersReadyRef = useRef(false);
  const hasFitBoundsRef = useRef(false);
  const prevSelectedIdRef = useRef<string | null>(null);

  const hotspotsRef = useRef(hotspots);
  const selectedRef = useRef(selectedHotspot);
  const visibleRef = useRef(visibleHotspotIds);
  const colorByRef = useRef(colorBy);
  const predictionsRef = useRef<Prediction[]>([]);
  const thresholdsRef = useRef(piiThresholds);
  const onSelectRef = useRef(onSelect);
  const onDeselectRef = useRef(onDeselect);

  hotspotsRef.current = hotspots;
  selectedRef.current = selectedHotspot;
  visibleRef.current = visibleHotspotIds;
  colorByRef.current = colorBy;
  predictionsRef.current = predictions;
  thresholdsRef.current = piiThresholds;
  onSelectRef.current = onSelect;
  onDeselectRef.current = onDeselect;

  const installLayersRef = useRef<(map: maplibregl.Map) => void>(() => {});
  const pushDataRef = useRef<(map: maplibregl.Map) => void>(() => {});

  installLayersRef.current = (map: maplibregl.Map) => {
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

    const colorField = colorByRef.current === 'risk' ? 'risk_level' : 'impact_score';
    const th = { critical: 60, high: 55, medium: 49 };
    const colExpr = severityColor(colorField, colorField === 'risk_level' ? undefined : th);

    map.addLayer({
      id: POLY_FILL_LAYER,
      type: 'fill',
      source: POLYGONS_SOURCE,
      paint: {
        'fill-color': colExpr,
        'fill-opacity': ['case', ['==', ['get', 'selected'], 1], 0.25, 0],
      },
    });

    map.addLayer({
      id: POLY_LINE_LAYER,
      type: 'line',
      source: POLYGONS_SOURCE,
      paint: {
        'line-color': colExpr,
        'line-width': ['case', ['==', ['get', 'selected'], 1], 4, 2],
        'line-opacity': ['case', ['==', ['get', 'selected'], 1], 1, 0.6],
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
        'circle-color': colExpr,
        'circle-opacity': ['case', ['==', ['get', 'dimmed'], 1], 0.15, 0.9],
        'circle-stroke-width': ['case', ['==', ['get', 'selected'], 1], 4, 1.5],
        'circle-stroke-color': ['case', ['==', ['get', 'selected'], 1], '#FFFFFF', COLORS.stroke],
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

    const pointsData = buildPointGeoJson(list, selectedId, visibleIds, colorByRef.current, predictionsRef.current);
    pointsSrc.setData(pointsData);

    const polyData = buildPolygonGeoJson(list, selectedId);
    polySrc.setData(polyData);

    // Update layer paint colors when colorBy or thresholds change
    const colorField = colorByRef.current === 'risk' ? 'risk_level' : 'impact_score';
    const th = thresholdsRef.current ?? { critical: 60, high: 55, medium: 49 };
    const colExpr = severityColor(colorField, colorField === 'risk_level' ? undefined : th);
    if (map.getLayer(POLY_FILL_LAYER)) map.setPaintProperty(POLY_FILL_LAYER, 'fill-color', colExpr);
    if (map.getLayer(POLY_LINE_LAYER)) map.setPaintProperty(POLY_LINE_LAYER, 'line-color', colExpr);
    if (map.getLayer(CIRCLES_LAYER)) map.setPaintProperty(CIRCLES_LAYER, 'circle-color', colExpr);

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

  const attachInteractions = (map: maplibregl.Map) => {
    const popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      className: 'custom-map-popup',
    });

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

    map.on('mouseenter', CIRCLES_LAYER, onMouseEnter);
    map.on('mouseleave', CIRCLES_LAYER, onMouseLeave);
    map.on('click', CIRCLES_LAYER, onClickCircle);
  };

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    layersReadyRef.current = false;
    hasFitBoundsRef.current = false;
    prevSelectedIdRef.current = selectedHotspot?.id ?? null;

    const map = new maplibregl.Map({
      container,
      style: DARK_STYLE,
      center: BENGALURU_CENTER,
      zoom: BENGALURU_ZOOM,
      maxZoom: 17,
      minZoom: 9,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    const setupLayers = () => {
      map.resize();
      installLayersRef.current(map);
      attachInteractions(map);
    };

    map.on('load', setupLayers);

    const ro = new ResizeObserver(() => map.resize());
    ro.observe(container);

    return () => {
      ro.disconnect();
      layersReadyRef.current = false;
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-push data when hotspots or visible filter changes (not selection)
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
  }, [hotspots, visibleHotspotIds, selectedHotspot, colorBy, piiThresholds]);

  // Fly to selected hotspot without re-pushing all data
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const currId = selectedHotspot?.id ?? null;
    const prevId = prevSelectedIdRef.current;
    prevSelectedIdRef.current = currId;

    if (currId && currId !== prevId) {
      const doFly = () => {
        if (map.loaded() && layersReadyRef.current) {
          map.flyTo({
            center: [selectedHotspot!.longitude, selectedHotspot!.latitude],
            zoom: 14.5,
            speed: 1.2,
            curve: 1.42,
            essential: true,
          });
        } else {
          const tryFly = () => {
            if (map.loaded() && layersReadyRef.current) {
              map.flyTo({
                center: [selectedHotspot!.longitude, selectedHotspot!.latitude],
                zoom: 14.5,
                speed: 1.2,
                curve: 1.42,
                essential: true,
              });
            } else {
              setTimeout(tryFly, 50);
            }
          };
          tryFly();
        }
      };
      doFly();
    }
  }, [selectedHotspot]);

  return (
    <div className="relative h-full min-h-[400px] w-full overflow-hidden rounded-xl border border-white/8 bg-[#070b16]">
      <div ref={containerRef} className="absolute inset-0 h-full w-full" />
      <div className="pointer-events-none absolute bottom-3 left-3 z-10 rounded-lg border border-white/8 bg-black/50 px-3 py-2 backdrop-blur-md">
        <div className="flex items-center gap-4 text-[11px] font-medium tracking-wide text-slate-300">
          {[
            { label: 'Critical', color: COLORS.critical },
            { label: 'High', color: COLORS.high },
            { label: 'Medium', color: COLORS.medium },
            { label: 'Low', color: COLORS.low },
          ].map((item) => (
            <span key={item.label} className="inline-flex items-center gap-2">
              <span
                className="h-2.5 w-2.5 rounded-full shadow-sm"
                style={{ backgroundColor: item.color }}
              />
              {item.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};