import React from 'react';
import { AlertTriangle, MapPin, ShieldAlert } from 'lucide-react';
import { DashboardSummary } from '../services/api';

interface KPIStatsProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

export const KPIStats: React.FC<KPIStatsProps> = ({ summary, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[1, 2, 3].map((n) => (
          <div key={n} className="glass-panel p-4 rounded-xl border border-white/5 animate-pulse">
            <div className="h-4 bg-white/10 rounded w-24 mb-2"></div>
            <div className="h-8 bg-white/10 rounded w-16"></div>
          </div>
        ))}
      </div>
    );
  }

  const kpis = [
    {
      title: "Total Violations",
      value: summary?.total_violations?.toLocaleString() || "0",
      icon: <AlertTriangle className="w-5 h-5 text-brand-teal" />,
      gradient: "from-brand-teal/10 to-transparent",
      borderColor: "border-brand-teal/20"
    },
    {
      title: "Active Hotspots",
      value: summary?.total_hotspots || "0",
      icon: <MapPin className="w-5 h-5 text-brand-gold" />,
      gradient: "from-brand-gold/10 to-transparent",
      borderColor: "border-brand-gold/20"
    },
    {
      title: "High-Risk Hotspots",
      value: summary?.high_risk_hotspots || "0",
      icon: <ShieldAlert className="w-5 h-5 text-severity-critical" />,
      gradient: "from-severity-critical/10 to-transparent",
      borderColor: "border-severity-critical/20"
    }
  ];

  return (
    <div className="grid grid-cols-3 gap-4 mb-6">
      {kpis.map((kpi, idx) => (
        <div 
          key={idx} 
          className={`glass-panel p-4 rounded-xl border ${kpi.borderColor} bg-gradient-to-br ${kpi.gradient} flex items-center justify-between transition-all duration-300 hover:scale-[1.02]`}
        >
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider block mb-1">
              {kpi.title}
            </span>
            <span className="text-2xl font-bold tracking-tight text-white">
              {kpi.value}
            </span>
          </div>
          <div className="p-3 bg-white/5 rounded-lg border border-white/10">
            {kpi.icon}
          </div>
        </div>
      ))}
    </div>
  );
};
