import React from 'react';
import { BrainCircuit, ChevronRight, Radar } from 'lucide-react';

import { Prediction } from '../services/api';
import { getRiskAppearanceFromLevel } from '../utils/risk';

interface PredictionsListProps {
  predictions: Prediction[];
  selectedId: string | null;
  onSelect: (prediction: Prediction) => void;
  loading: boolean;
}

export const PredictionsList: React.FC<PredictionsListProps> = ({
  predictions,
  selectedId,
  onSelect,
  loading,
}) => {
  const sortedPredictions = [...predictions].sort((a, b) => b.risk_score - a.risk_score);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-2">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-teal border-t-transparent"></div>
          <span className="text-sm">Loading predictions...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
        <div>
          <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-brand-gold">
            <BrainCircuit className="h-3.5 w-3.5" />
            Tomorrow&apos;s High-Risk Zones
          </p>
          <p className="text-xs text-slate-400">
            Next-day risk forecast for current operating zones
          </p>
        </div>
        <div className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-300">
          {sortedPredictions.length} Zones
        </div>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {sortedPredictions.length === 0 ? (
          <div className="rounded-xl border border-dashed border-white/10 bg-brand-blue/20 p-4 text-center text-sm text-slate-400">
            No prediction results are available.
          </div>
        ) : (
          sortedPredictions.map((prediction) => {
            const risk = getRiskAppearanceFromLevel(prediction.risk_level);
            const isSelected = selectedId === prediction.hotspot_id;

            return (
              <button
                key={`${prediction.hotspot_id}-${prediction.prediction_horizon}`}
                type="button"
                onClick={() => onSelect(prediction)}
                className={`w-full rounded-xl border p-4 text-left transition-all duration-200 ${
                  isSelected
                    ? `bg-brand-teal/10 ${risk.border} shadow-premium`
                    : 'bg-brand-blue/35 border-white/5 hover:border-white/20'
                }`}
              >
                <div className="mb-2 flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-white" title={prediction.hotspot_name}>
                      {prediction.hotspot_name}
                    </p>
                    <p className="mt-1 flex items-center gap-1 text-[10px] uppercase tracking-wider text-slate-400">
                      <Radar className="h-3 w-3" />
                      {prediction.prediction_horizon}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${risk.bg} ${risk.textCol}`}>
                      {prediction.risk_level}
                    </span>
                    <ChevronRight className="h-4 w-4 text-slate-500" />
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Risk Score</span>
                  <span className={`font-extrabold ${risk.textCol}`}>
                    {prediction.risk_score}
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
};
