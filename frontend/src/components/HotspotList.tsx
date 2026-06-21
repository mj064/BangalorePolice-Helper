import React from 'react';
import { Hotspot } from '../services/api';

interface HotspotListProps {
  hotspots: Hotspot[];
  selectedId: string | null;
  onSelect: (hotspot: Hotspot) => void;
  loading: boolean;
  compact?: boolean;
}

const getSeverityLabel = (score: number): { text: string; bg: string; textCol: string } => {
  if (score >= 66) return { text: 'Critical', bg: 'bg-severity-critical/15', textCol: 'text-severity-critical' };
  if (score >= 56) return { text: 'High',     bg: 'bg-severity-high/15',     textCol: 'text-severity-high'     };
  if (score >= 46) return { text: 'Medium',   bg: 'bg-severity-medium/15',   textCol: 'text-severity-medium'   };
  return               { text: 'Low',      bg: 'bg-severity-low/15',      textCol: 'text-severity-low'      };
};

export const HotspotList: React.FC<HotspotListProps> = ({
  hotspots,
  selectedId,
  onSelect,
  loading,
  compact = false,
}) => {
  if (loading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center text-slate-400">
        <div className="mb-2 h-8 w-8 animate-spin rounded-full border-4 border-brand-teal border-t-transparent" />
        <span>Loading hotspot details...</span>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className={`flex-1 overflow-y-auto scrollbar-thin ${compact ? 'space-y-2 p-3' : 'space-y-3 p-4'}`}>
        {hotspots.length === 0 ? (
          <div className="py-8 text-center text-sm text-slate-400">
            No hotspots match the filter parameters.
          </div>
        ) : (
          hotspots.map((hotspot) => {
            const sev = getSeverityLabel(hotspot.impact_score);
            const isSelected = selectedId === hotspot.id;

            return (
              <div
                key={hotspot.id}
                onClick={() => onSelect(hotspot)}
                className={`cursor-pointer rounded-xl border transition-all duration-200 ${
                  compact ? 'p-3' : 'p-4'
                } ${
                  isSelected
                    ? 'border-brand-teal bg-brand-teal/10 shadow-premium'
                    : 'border-white/5 bg-brand-blue/40 hover:border-white/20'
                }`}
              >
                <div className="mb-1.5 flex items-start justify-between gap-2">
                  <h3 className="max-w-[70%] truncate text-sm font-semibold text-white">
                    {hotspot.name}
                  </h3>
                  <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${sev.bg} ${sev.textCol}`}>
                    {compact ? sev.text : `${sev.text} (PII: ${hotspot.impact_score})`}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>
                    Violations: <strong className="text-white">{hotspot.violations}</strong>
                  </span>
                  {compact ? (
                    <span className="text-[10px] font-semibold text-slate-300">
                      PII {hotspot.impact_score}
                    </span>
                  ) : (
                    <span className="text-[10px] font-medium tracking-tight">
                      {hotspot.latitude.toFixed(4)}, {hotspot.longitude.toFixed(4)}
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
