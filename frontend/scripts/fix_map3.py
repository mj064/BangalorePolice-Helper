import pathlib

p = pathlib.Path('frontend/src/maps/HotspotMap.tsx')
t = p.read_text('utf-8')

# 1) restore Prediction import
if 'import { Hotspot, Prediction }' not in t:
    t = t.replace("import { Hotspot } from '../services/api';\n",
                  "import { Hotspot, Prediction } from '../services/api';\n")

# 2) restore props + destructuring + refs + buildPointGeoJson + installLayers coloring
old_props = '''interface HotspotMapProps {
  hotspots: Hotspot[];
  selectedHotspot: Hotspot | null;
  onSelect: (hotspot: Hotspot) => void;
  onDeselect: () => void;
  visibleHotspotIds?: Set<string> | null;
}

const BENGALURU_CENTER'''
new_props = '''interface HotspotMapProps {
  hotspots: Hotspot[];
  selectedHotspot: Hotspot | null;
  predictions: Prediction[];
  onSelect: (hotspot: Hotspot) => void;
  onDeselect: () => void;
  visibleHotspotIds?: Set<string> | null;
  colorBy?: 'pii' | 'risk';
  piiThresholds?: { critical: number; high: number; medium: number };
}

const BENGALURU_CENTER'''
t = t.replace(old_props, new_props)

old_destructure = '''export const HotspotMap: React.FC<HotspotMapProps> = ({
  hotspots,
  selectedHotspot,
  
  onSelect,
  onDeselect,
  visibleHotspotIds = null,
}) => {'''
new_destructure = '''export const HotspotMap: React.FC<HotspotMapProps> = ({
  hotspots,
  selectedHotspot,
  predictions,
  onSelect,
  onDeselect,
  visibleHotspotIds = null,
  colorBy = 'pii',
  piiThresholds,
}) => {'''
t = t.replace(old_destructure, new_destructure)

old_refs = '''  const hotspotsRef = useRef(hotspots);
  const selectedRef = useRef(selectedHotspot);
  const visibleRef = useRef(visibleHotspotIds);
  const onSelectRef = useRef(onSelect);
  const onDeselectRef = useRef(onDeselect);

  hotspotsRef.current = hotspots;
  selectedRef.current = selectedHotspot;
  visibleRef.current = visibleHotspotIds;
  onSelectRef.current = onSelect;
  onDeselectRef.current = onDeselect;'''
new_refs = '''  const hotspotsRef = useRef(hotspots);
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
  onDeselectRef.current = onDeselect;'''
t = t.replace(old_refs, new_refs)

old_color = '''    const scores = hotspotsRef.current.map((h) => h.impact_score);
    const th = computePiiThresholds(scores as number[]);
    const colExpr = severityColor('impact_score', th);'''
new_color = '''    const scores = hotspotsRef.current.map((h) => h.impact_score);
    const th = thresholdsRef.current ?? computePiiThresholds(scores);
    const colorField = colorByRef.current === 'risk' ? 'risk_level' : 'impact_score';
    const colExpr = severityColor(colorField, th);'''
t = t.replace(old_color, new_color)

old_call = '''    const pointsData = buildPointGeoJson(list, selectedId, visibleIds);'''
new_call = '''    const pointsData = buildPointGeoJson(list, selectedId, visibleIds, colorByRef.current, predictionsRef.current);'''
t = t.replace(old_call, new_call)

old_build = '''function buildPointGeoJson(
  hotspots: Hotspot[],
  selectedId: string | null,
  visibleIds: Set<string> | null,
): GeoJSON.FeatureCollection {
  const list = visibleIds !== null ? hotspots.filter((h) => visibleIds.has(h.id)) : hotspots;
  return {
    type: 'FeatureCollection',
    features: list.map((h) => {
      const isSelected = selectedId === h.id;
      const dimmed = selectedId !== null && !isSelected;
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
}'''
new_build = '''function buildPointGeoJson(
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
}'''
t = t.replace(old_build, new_build)

p.write_text(t, encoding='utf-8')
print('patched')