import axios from 'axios';

// All numbers are `number` in TypeScript. These aliases improve readability.
type int = number;
type float = number;

// ---------------------------------------------------------------------------
// Response shapes matching the FastAPI schemas
// ---------------------------------------------------------------------------

export interface DashboardSummary {
  total_violations: int;
  total_hotspots: int;
  high_risk_hotspots: int;
}

export interface Hotspot {
  id: string;
  name: string;
  latitude: float;
  longitude: float;
  violations: int;
  impact_score: int;
  polygon: string | null;
}

export interface HotspotDetail extends Hotspot {
  violation_density: float;
  main_road_score: float;
  peak_hour_score: float;
  repeat_violation_score: float;
  trend: string;
  h3_cell: string;
  vehicle_distribution: Record<string, int>;
  violation_type_distribution: Record<string, int>;
  hourly_distribution: Record<string, int>;
}

export interface Prediction {
  hotspot_id: string;
  hotspot_name: string;
  risk_score: int;
  risk_level: string;
  prediction_horizon: string;
}

export interface Recommendation {
  hotspot_id: string;
  hotspot_name: string;
  priority: string;
  officers: int;
  tow_vehicles: int;
  deployment_window: string;
  reason: string;
}

// ---------------------------------------------------------------------------
// API client — use full Render URL as fallback so Vercel env var isn't needed
// ---------------------------------------------------------------------------

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://bangalorepolice-helper.onrender.com/api';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

export const apiService = {
  getSummary: async (): Promise<DashboardSummary> => {
    const { data } = await client.get('/dashboard/summary');
    return data as DashboardSummary;
  },

  getHotspots: async (): Promise<Hotspot[]> => {
    const { data } = await client.get('/hotspots');
    return data as Hotspot[];
  },

  getHotspot: async (id: string): Promise<HotspotDetail> => {
    const { data } = await client.get(`/hotspots/${id}`);
    return data as HotspotDetail;
  },

  getPredictions: async (): Promise<Prediction[]> => {
    const { data } = await client.get('/predictions');
    return data as Prediction[];
  },

  getRecommendations: async (): Promise<Recommendation[]> => {
    const { data } = await client.get('/recommendations');
    return data as Recommendation[];
  },
};
