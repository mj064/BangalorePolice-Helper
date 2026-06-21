import React from 'react';
import { Clock, ShieldCheck, Truck, Users } from 'lucide-react';

import { Recommendation } from '../services/api';
import { getRiskAppearanceFromLevel } from '../utils/risk';

interface RecommendationsListProps {
  recommendations: Recommendation[];
  loading: boolean;
}

export const RecommendationsList: React.FC<RecommendationsListProps> = ({
  recommendations,
  loading,
}) => {
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-2">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-teal border-t-transparent"></div>
          <span className="text-sm">Loading recommendations...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
        <div>
          <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-brand-gold">
            <ShieldCheck className="h-3.5 w-3.5" />
            Recommended Enforcement Actions
          </p>
          <p className="text-xs text-slate-400">
            Officer and tow deployment by hotspot priority
          </p>
        </div>
        <div className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-300">
          {recommendations.length} Actions
        </div>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {recommendations.length === 0 ? (
          <div className="rounded-xl border border-dashed border-white/10 bg-brand-blue/20 p-4 text-center text-sm text-slate-400">
            No enforcement recommendations are available.
          </div>
        ) : (
          recommendations.map((recommendation) => {
            const priority = getRiskAppearanceFromLevel(recommendation.priority);

            return (
              <article
                key={recommendation.hotspot_id}
                className={`rounded-xl border bg-brand-blue/35 p-4 ${priority.border}`}
              >
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-white" title={recommendation.hotspot_name}>
                      {recommendation.hotspot_name}
                    </p>
                    <p className="mt-1 line-clamp-2 text-xs text-slate-400">
                      {recommendation.reason}
                    </p>
                  </div>
                  <span className={`shrink-0 rounded px-2 py-0.5 text-[10px] font-bold ${priority.bg} ${priority.textCol}`}>
                    {recommendation.priority}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="rounded-lg border border-white/5 bg-white/[0.03] p-2">
                    <p className="mb-1 flex items-center gap-1 text-[10px] uppercase tracking-wider text-slate-500">
                      <Users className="h-3 w-3" />
                      Officers
                    </p>
                    <p className="font-extrabold text-white">{recommendation.officers}</p>
                  </div>
                  <div className="rounded-lg border border-white/5 bg-white/[0.03] p-2">
                    <p className="mb-1 flex items-center gap-1 text-[10px] uppercase tracking-wider text-slate-500">
                      <Truck className="h-3 w-3" />
                      Tow
                    </p>
                    <p className="font-extrabold text-white">{recommendation.tow_vehicles}</p>
                  </div>
                  <div className="rounded-lg border border-white/5 bg-white/[0.03] p-2">
                    <p className="mb-1 flex items-center gap-1 text-[10px] uppercase tracking-wider text-slate-500">
                      <Clock className="h-3 w-3" />
                      Window
                    </p>
                    <p className={`font-extrabold ${priority.textCol}`}>
                      {recommendation.deployment_window}
                    </p>
                  </div>
                </div>
              </article>
            );
          })
        )}
      </div>
    </div>
  );
};
