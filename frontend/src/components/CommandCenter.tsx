import React, { useEffect, useMemo, useState } from 'react';
import { ChevronDown, Shield, Target } from 'lucide-react';

import { Hotspot, Prediction, Recommendation } from '../services/api';
import {
  DeploymentAction,
  getTopPriorityDeployments,
  mergePredictionsAndRecommendations,
} from '../utils/command';
import { HotspotList } from './HotspotList';
import { TopPriorityDeployments } from './TopPriorityDeployments';

export type CommandTab = 'deployments' | 'zones';

const getSeverityCategory = (score: number): string => {
  if (score >= 66) return 'CRITICAL';
  if (score >= 56) return 'HIGH';
  if (score >= 46) return 'MEDIUM';
  return 'LOW';
};

const PRIORITY_ORDER: Record<string, number> = {
  Critical: 4, High: 3, Medium: 2, Low: 1,
};

export interface CommandCenterFilter {
  visibleHotspotIds: Set<string> | null;
}

interface CommandCenterProps {
  hotspots: Hotspot[];
  predictions: Prediction[];
  recommendations: Recommendation[];
  selectedHotspotId: string | null;
  selectedDeploymentId: string | null;
  onSelectHotspot: (hotspot: Hotspot) => void;
  onSelectDeployment: (deployment: DeploymentAction) => void;
  onFilterChange: (filter: CommandCenterFilter) => void;
  loadingHotspots: boolean;
  loadingOperations: boolean;
  // Lifted search / filter / sort / tab from DashboardPage
  activeTab: CommandTab;
  onTabChange: (tab: CommandTab) => void;
  search: string;
  severityFilter: string;
  sortBy: string;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({
  hotspots,
  predictions,
  recommendations,
  selectedHotspotId,
  selectedDeploymentId,
  onSelectHotspot,
  onSelectDeployment,
  onFilterChange,
  loadingHotspots,
  loadingOperations,
  activeTab,
  onTabChange,
  search,
  severityFilter,
  sortBy,
}) => {
  const [showAllDeployments, setShowAllDeployments] = useState(false);

  // ── Merged deployment data ──────────────────────────────────────────────
  const deployments = useMemo(
    () => mergePredictionsAndRecommendations(predictions, recommendations),
    [predictions, recommendations],
  );

  const deploymentByHotspotId = useMemo(
    () => new Map(deployments.map((d) => [d.hotspot_id, d])),
    [deployments],
  );

  // ── Filtered + sorted zones ─────────────────────────────────────────────
  const filteredHotspots = useMemo(() => {
    const q = search.trim().toLowerCase();
    return hotspots
      .filter((h) => {
        if (severityFilter !== 'ALL' && getSeverityCategory(h.impact_score) !== severityFilter) return false;
        if (!q) return true;
        const dep = deploymentByHotspotId.get(h.id);
        return [h.id, h.name, dep?.priority ?? '', dep?.deployment_window ?? '', dep?.reason ?? '']
          .join(' ').toLowerCase().includes(q);
      })
      .sort((a, b) => {
        if (sortBy === 'VIOLATIONS') return b.violations - a.violations;
        return b.impact_score - a.impact_score;
      });
  }, [hotspots, search, severityFilter, sortBy, deploymentByHotspotId]);

  // ── Filtered + sorted deployments ──────────────────────────────────────
  const filteredDeployments = useMemo(() => {
    const q = search.trim().toLowerCase();
    return deployments
      .filter((d) => {
        if (severityFilter !== 'ALL') {
          const h = hotspots.find((x) => x.id === d.hotspot_id);
          if (!h || getSeverityCategory(h.impact_score) !== severityFilter) return false;
        }
        if (!q) return true;
        return [d.hotspot_id, d.hotspot_name, d.priority, d.deployment_window, d.reason]
          .join(' ').toLowerCase().includes(q);
      })
      .sort((a, b) => {
        if (sortBy === 'RISK') return b.risk_score - a.risk_score;
        if (sortBy === 'VIOLATIONS') {
          const vA = hotspots.find((h) => h.id === a.hotspot_id)?.violations ?? 0;
          const vB = hotspots.find((h) => h.id === b.hotspot_id)?.violations ?? 0;
          return vB - vA;
        }
        const pd = (PRIORITY_ORDER[b.priority] ?? 0) - (PRIORITY_ORDER[a.priority] ?? 0);
        return pd !== 0 ? pd : b.risk_score - a.risk_score;
      });
  }, [deployments, hotspots, search, severityFilter, sortBy]);

  // ── Notify parent of visible hotspot IDs for map sync ──────────────────
  useEffect(() => {
    const isFiltered = search.trim() !== '' || severityFilter !== 'ALL';
    if (!isFiltered) { onFilterChange({ visibleHotspotIds: null }); return; }
    onFilterChange({ visibleHotspotIds: new Set(filteredHotspots.map((h) => h.id)) });
  }, [filteredHotspots, search, severityFilter, onFilterChange]);

  const visibleDeployments = showAllDeployments
    ? filteredDeployments
    : getTopPriorityDeployments(filteredDeployments, 5);

  const criticalCount = deployments.filter((d) => d.priority === 'Critical').length;
  const hasFilter = search.trim() !== '' || severityFilter !== 'ALL';

  return (
    <aside className="command-rail flex h-full w-full flex-col border-r border-white/8 bg-[#0a1020]/95 md:w-[380px] md:flex-none">

      {/* ── KPI cards + tab switcher ─────────────────────────────────── */}
      <div className="border-b border-white/8 px-4 py-4">
        <div className="mb-3 flex items-center gap-2">
          <div className="rounded-md border border-brand-teal/20 bg-brand-teal/10 p-1.5">
            <Target className="h-4 w-4 text-brand-teal" />
          </div>
          <div>
            <h2 className="text-sm font-semibold tracking-wide text-white">Command Center</h2>
            <p className="text-[11px] text-slate-400">AI-ranked enforcement for tomorrow</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="command-card px-3 py-2">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Critical Queue</p>
            <p className="text-lg font-semibold tabular-nums text-severity-critical">
              {loadingOperations ? '—' : criticalCount}
            </p>
          </div>
          <div className="command-card px-3 py-2">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Total Actions</p>
            <p className="text-lg font-semibold tabular-nums text-white">
              {loadingOperations ? '—' : deployments.length}
            </p>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="mt-3 grid grid-cols-2 gap-1 rounded-xl border border-white/8 bg-black/30 p-1">
          {(['deployments', 'zones'] as CommandTab[]).map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => onTabChange(tab)}
              className={`rounded-lg px-3 py-2.5 text-[11px] font-bold uppercase tracking-wider transition ${
                activeTab === tab
                  ? 'border border-brand-teal/25 bg-brand-teal/15 text-brand-teal shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab === 'deployments' ? 'Deployments' : 'All Zones'}
            </button>
          ))}
        </div>
      </div>

      {/* ── Tab content ──────────────────────────────────────────────── */}
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        {activeTab === 'deployments' ? (
          <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
            <div className="border-b border-white/8 px-4 py-3">
              <div className="flex items-center justify-between gap-2">
                <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-brand-gold">
                  <Shield className="h-3.5 w-3.5" />
                  {showAllDeployments ? 'All Deployments' : 'Top Priority Deployments'}
                </p>
                <span className="rounded-md border border-white/8 px-2 py-1 text-[10px] font-semibold text-slate-300">
                  {visibleDeployments.length}
                  {hasFilter && filteredDeployments.length < deployments.length && (
                    <span className="ml-1 text-slate-500">/ {deployments.length}</span>
                  )}
                </span>
              </div>
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3 scrollbar-thin">
              <TopPriorityDeployments
                deployments={visibleDeployments}
                selectedId={selectedDeploymentId}
                onSelect={onSelectDeployment}
                loading={loadingOperations}
              />
              {!loadingOperations && filteredDeployments.length > 5 && (
                <button
                  type="button"
                  onClick={() => setShowAllDeployments((v) => !v)}
                  className="mt-3 flex w-full items-center justify-center gap-1 rounded-lg border border-white/8 px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-300 transition hover:bg-white/[0.03]"
                >
                  {showAllDeployments
                    ? 'Show Top 5 Only'
                    : `View All ${filteredDeployments.length} Actions`}
                  <ChevronDown className={`h-3.5 w-3.5 transition ${showAllDeployments ? 'rotate-180' : ''}`} />
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="min-h-0 flex-1 overflow-hidden">
            <HotspotList
              hotspots={filteredHotspots}
              selectedId={selectedHotspotId}
              onSelect={onSelectHotspot}
              loading={loadingHotspots}
              compact
            />
          </div>
        )}
      </div>
    </aside>
  );
};
