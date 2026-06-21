import React from 'react';
import { Clock, MapPin, Truck, Users } from 'lucide-react';

import { DeploymentAction } from '../utils/command';
import { getRiskAppearanceFromLevel } from '../utils/risk';

interface TopPriorityDeploymentsProps {
  deployments: DeploymentAction[];
  selectedId: string | null;
  onSelect: (deployment: DeploymentAction) => void;
  loading: boolean;
}

export const TopPriorityDeployments: React.FC<TopPriorityDeploymentsProps> = ({
  deployments,
  selectedId,
  onSelect,
  loading,
}) => {
  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="command-card animate-pulse p-4">
            <div className="mb-2 h-3 w-24 rounded bg-white/10" />
            <div className="h-4 w-40 rounded bg-white/10" />
          </div>
        ))}
      </div>
    );
  }

  if (deployments.length === 0) {
    return (
      <div className="command-card border-dashed p-4 text-center text-sm text-slate-400">
        No deployments match the current filters.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {deployments.map((deployment, index) => {
        const priority = getRiskAppearanceFromLevel(deployment.priority);
        const isSelected = selectedId === deployment.hotspot_id;

        return (
          <button
            key={deployment.hotspot_id}
            type="button"
            onClick={() => onSelect(deployment)}
            className={`w-full rounded-lg border p-3 text-left transition-all duration-200 ${
              isSelected
                ? 'border-brand-teal bg-brand-teal/5 shadow-md shadow-brand-teal/10'
                : 'border-white/5 bg-white/[0.02] hover:border-white/10 hover:bg-white/[0.04]'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-[10px] font-medium text-slate-500">
                    #{index + 1}
                  </span>
                  {isSelected && (
                    <span className="relative flex h-1.5 w-1.5">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-teal opacity-75" />
                      <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-brand-teal" />
                    </span>
                  )}
                </div>
                <p className="truncate text-sm font-semibold tracking-wide text-white" title={deployment.hotspot_name}>
                  {deployment.hotspot_name}
                </p>
                <div className="mt-1.5 flex items-center gap-3 text-[11px] text-slate-400">
                  <span className="inline-flex items-center gap-1.5 font-medium">
                    <MapPin className="h-3 w-3 text-slate-500" />
                    Risk {deployment.risk_score}
                  </span>
                  <span className="text-slate-500">{deployment.prediction_horizon}</span>
                </div>
              </div>
              <span className={`shrink-0 rounded-md px-2.5 py-1 text-[10px] font-bold tracking-wide ${priority.bg} ${priority.textCol}`}>
                {deployment.priority}
              </span>
            </div>

            {isSelected && (
              <div className="mt-4 grid grid-cols-3 gap-2 text-[11px] animate-in fade-in slide-in-from-top-1 duration-200">
                <div className="rounded-md border border-white/5 bg-black/40 px-2.5 py-2">
                  <p className="mb-1 flex items-center gap-1.5 text-[9px] font-medium uppercase tracking-wider text-slate-500">
                    <Users className="h-3 w-3" /> Officers
                  </p>
                  <p className="text-sm font-bold text-white">{deployment.officers}</p>
                </div>
                <div className="rounded-md border border-white/5 bg-black/40 px-2.5 py-2">
                  <p className="mb-1 flex items-center gap-1.5 text-[9px] font-medium uppercase tracking-wider text-slate-500">
                    <Truck className="h-3 w-3" /> Tow
                  </p>
                  <p className="text-sm font-bold text-white">{deployment.tow_vehicles}</p>
                </div>
                <div className="rounded-md border border-white/5 bg-black/40 px-2.5 py-2">
                  <p className="mb-1 flex items-center gap-1.5 text-[9px] font-medium uppercase tracking-wider text-slate-500">
                    <Clock className="h-3 w-3" /> Window
                  </p>
                  <p className={`text-xs font-bold ${priority.textCol}`}>{deployment.deployment_window}</p>
                </div>
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
};
