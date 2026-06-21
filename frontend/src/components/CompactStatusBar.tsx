import React from 'react';
import { DashboardSummary, Prediction } from '../services/api';

interface CompactStatusBarProps {
  summary: DashboardSummary | null;
  predictions: Prediction[];
  loading: boolean;
}

export const CompactStatusBar: React.FC<CompactStatusBarProps> = ({
  summary,
  predictions,
  loading,
}) => {
  const criticalActions = predictions.filter(
    (prediction) => prediction.risk_level === 'Critical' || prediction.risk_level === 'High',
  ).length;

  const stats = [
    {
      label: 'Violations',
      value: summary?.total_violations?.toLocaleString() ?? '—',
    },
    {
      label: 'Hotspots',
      value: summary?.total_hotspots?.toLocaleString() ?? '—',
    },
    {
      label: 'Tomorrow Critical/High',
      value: loading ? '—' : String(criticalActions),
    },
  ];

  return (
    <div className="hidden items-center gap-1 rounded-lg border border-white/8 bg-white/[0.03] p-1 md:flex">
      {stats.map((stat, index) => (
        <React.Fragment key={stat.label}>
          {index > 0 && <span className="mx-1 h-4 w-px bg-white/10" />}
          <div className="px-3 py-1.5">
            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-slate-500">
              {stat.label}
            </p>
            <p className="text-sm font-semibold tabular-nums text-white">{stat.value}</p>
          </div>
        </React.Fragment>
      ))}
    </div>
  );
};
