import React from 'react';
import { AlertOctagon, Activity, Gauge } from 'lucide-react';

import { Prediction } from '../services/api';

interface PredictionKPIStatsProps {
  predictions: Prediction[];
  loading: boolean;
}

export const PredictionKPIStats: React.FC<PredictionKPIStatsProps> = ({
  predictions,
  loading,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-3 gap-3">
        {[1, 2, 3].map((n) => (
          <div key={n} className="glass-panel p-3 rounded-xl border border-white/5 animate-pulse">
            <div className="h-3 bg-white/10 rounded w-20 mb-2"></div>
            <div className="h-6 bg-white/10 rounded w-12"></div>
          </div>
        ))}
      </div>
    );
  }

  const highestRisk = predictions.length > 0 ? Math.max(...predictions.map((p) => p.risk_score)) : 0;
  const highRiskCount = predictions.filter((p) => p.risk_level === 'Critical' || p.risk_level === 'High').length;
  const averageRisk = predictions.length > 0
    ? Math.round(predictions.reduce((sum, prediction) => sum + prediction.risk_score, 0) / predictions.length)
    : 0;

  const cards = [
    {
      title: 'Highest Predicted Risk',
      value: highestRisk,
      icon: <AlertOctagon className="w-4 h-4 text-severity-critical" />,
      border: 'border-severity-critical/20',
      glow: 'from-severity-critical/10 to-transparent',
    },
    {
      title: 'Predicted High-Risk Zones',
      value: highRiskCount,
      icon: <Activity className="w-4 h-4 text-severity-high" />,
      border: 'border-severity-high/20',
      glow: 'from-severity-high/10 to-transparent',
    },
    {
      title: 'Average Prediction Risk',
      value: averageRisk,
      icon: <Gauge className="w-4 h-4 text-brand-gold" />,
      border: 'border-brand-gold/20',
      glow: 'from-brand-gold/10 to-transparent',
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-3">
      {cards.map((card) => (
        <div
          key={card.title}
          className={`glass-panel rounded-xl border ${card.border} bg-gradient-to-br ${card.glow} p-3`}
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-[9px] uppercase tracking-wider text-slate-400 font-bold">
                {card.title}
              </p>
              <p className="text-xl font-extrabold text-white leading-tight">
                {card.value}
              </p>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/5 p-2">
              {card.icon}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
