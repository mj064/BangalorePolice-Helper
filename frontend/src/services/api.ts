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
// API client
// ---------------------------------------------------------------------------

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const apiService = {
  getSummary: async (): Promise<DashboardSummary> => {
    const res = await axios.get<DashboardSummary>(`${API_BASE_URL}/dashboard/summary`);
    return res.data;
  },

  getHotspots: async (): Promise<Hotspot[]> => {
    const res = await axios.get<Hotspot[]>(`${API_BASE_URL}/hotspots`);
    return res.data;
  },

  getHotspot: async (id: string): Promise<HotspotDetail> => {
    const res = await axios.get<HotspotDetail>(`${API_BASE_URL}/hotspots/${id}`);
    return res.data;
  },

  getPredictions: async (): Promise<Prediction[]> => {
    const res = await axios.get<Prediction[]>(`${API_BASE_URL}/predictions`);
    return res.data;
  },

  getRecommendations: async (): Promise<Recommendation[]> => {
    const res = await axios.get<Recommendation[]>(`${API_BASE_URL}/recommendations`);
    return res.data;
  },
};
