import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowUpDown, Compass, Search, X } from 'lucide-react';
import { apiService, Hotspot, DashboardSummary, Prediction, Recommendation } from '../services/api';
import { CommandCenter, CommandCenterFilter, CommandTab } from '../components/CommandCenter';
import { HotspotMap } from '../maps/HotspotMap';
import { HotspotDetailsPanel } from '../components/HotspotDetailsPanel';
import { DeploymentAction } from '../utils/command';

interface SelectedDashboardItem {
  hotspot: Hotspot | null;
  prediction: Prediction | null;
  recommendation: Recommendation | null;
  source: 'hotspot' | 'deployment';
}

// Sort options change based on which tab is active
const SORT_OPTIONS: Record<CommandTab, { value: string; label: string }[]> = {
  deployments: [
    { value: 'PRIORITY',   label: 'Priority'   },
    { value: 'RISK',       label: 'Risk Score' },
    { value: 'VIOLATIONS', label: 'Violations' },
  ],
  zones: [
    { value: 'SCORE',      label: 'PII Score'  },
    { value: 'VIOLATIONS', label: 'Violations' },
  ],
};

export const DashboardPage: React.FC = () => {
  // ── Data state ─────────────────────────────────────────────────────────
  const [summary,         setSummary]         = useState<DashboardSummary | null>(null);
  const [hotspots,        setHotspots]        = useState<Hotspot[]>([]);
  const [predictions,     setPredictions]     = useState<Prediction[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [selectedItem,    setSelectedItem]    = useState<SelectedDashboardItem | null>(null);
  const [visibleHotspotIds, setVisibleHotspotIds] = useState<Set<string> | null>(null);

  const piiThresholds = useMemo(() => {
    const scores = hotspots.map((h) => h.impact_score);
    if (!scores.length) return undefined;
    const sorted = [...scores].sort((a, b) => a - b);
    const max = sorted[sorted.length - 1];
    return {
      critical: Math.max(max - 5, Math.round(max * 0.85)),
      high: Math.max(max - 10, Math.round(max * 0.7)),
      medium: Math.max(max - 20, Math.round(max * 0.55)),
    };
  }, [hotspots]);

  const [loadingSummary,         setLoadingSummary]         = useState(true);
  const [loadingHotspots,        setLoadingHotspots]        = useState(true);
  const [loadingPredictions,     setLoadingPredictions]     = useState(true);
  const [loadingRecommendations, setLoadingRecommendations] = useState(true);

  // ── Search / filter / sort / tab — lifted to page so header can render them ──
  const [activeTab,      setActiveTab]      = useState<CommandTab>('deployments');
  const [rawSearch,      setRawSearch]      = useState('');
  const [search,         setSearch]         = useState('');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [sortBy,         setSortBy]         = useState('PRIORITY');

  // Debounce search 300ms
  useEffect(() => {
    const t = setTimeout(() => setSearch(rawSearch), 300);
    return () => clearTimeout(t);
  }, [rawSearch]);

  // When switching tabs reset sort to tab default, but only if current sort
  // doesn't belong to the new tab's options
  const handleTabChange = (tab: CommandTab) => {
    setActiveTab(tab);
    const validValues = SORT_OPTIONS[tab].map((o) => o.value);
    if (!validValues.includes(sortBy)) {
      setSortBy(SORT_OPTIONS[tab][0].value);
    }
  };

  // ── Data loading (retry once if backend wasn't ready on first paint) ───
  useEffect(() => {
    let cancelled = false;

    const loadCore = async (attempt = 0) => {
      try {
        const [summaryData, hotspotData] = await Promise.all([
          apiService.getSummary(),
          apiService.getHotspots(),
        ]);
        if (cancelled) return;
        setSummary(summaryData);
        setHotspots(hotspotData);
      } catch (e) {
        console.error('dashboard core fetch', e);
        if (!cancelled && attempt === 0) {
          window.setTimeout(() => { void loadCore(1); }, 1500);
        }
      } finally {
        if (!cancelled) {
          setLoadingSummary(false);
          setLoadingHotspots(false);
        }
      }
    };

    void loadCore();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadOperations = async (attempt = 0) => {
      try {
        const [predictionData, recommendationData] = await Promise.all([
          apiService.getPredictions(),
          apiService.getRecommendations(),
        ]);
        if (cancelled) return;
        setPredictions(predictionData);
        setRecommendations(recommendationData);
      } catch (e) {
        console.error('dashboard operations fetch', e);
        if (!cancelled && attempt === 0) {
          window.setTimeout(() => { void loadOperations(1); }, 1500);
        }
      } finally {
        if (!cancelled) {
          setLoadingPredictions(false);
          setLoadingRecommendations(false);
        }
      }
    };

    const t = window.setTimeout(() => { void loadOperations(); }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(t);
    };
  }, []);

  // ── Selection handlers ─────────────────────────────────────────────────
  const handleSelectHotspot = (hotspot: Hotspot) => {
    setSelectedItem({
      hotspot,
      prediction:     predictions.find((p) => p.hotspot_id === hotspot.id) || null,
      recommendation: recommendations.find((r) => r.hotspot_id === hotspot.id) || null,
      source: 'hotspot',
    });
  };

  // Re-resolve when predictions/recommendations finish lazy-loading
  useEffect(() => {
    setSelectedItem((prev) => {
      if (!prev || prev.source !== 'hotspot' || !prev.hotspot) return prev;
      const p = predictions.find((x) => x.hotspot_id === prev.hotspot!.id) || null;
      const r = recommendations.find((x) => x.hotspot_id === prev.hotspot!.id) || null;
      if (p === prev.prediction && r === prev.recommendation) return prev;
      return { ...prev, prediction: p, recommendation: r };
    });
  }, [predictions, recommendations]);

  const handleSelectDeployment = (deployment: DeploymentAction) => {
    setSelectedItem({
      hotspot: hotspots.find((h) => h.id === deployment.hotspot_id) || null,
      prediction: predictions.find((p) => p.hotspot_id === deployment.hotspot_id) || {
        hotspot_id: deployment.hotspot_id,
        hotspot_name: deployment.hotspot_name,
        risk_score: deployment.risk_score,
        risk_level: deployment.risk_level,
        prediction_horizon: deployment.prediction_horizon,
      },
      recommendation: recommendations.find((r) => r.hotspot_id === deployment.hotspot_id) || {
        hotspot_id: deployment.hotspot_id,
        hotspot_name: deployment.hotspot_name,
        priority: deployment.priority,
        officers: deployment.officers,
        tow_vehicles: deployment.tow_vehicles,
        deployment_window: deployment.deployment_window,
        reason: deployment.reason,
      },
      source: 'deployment',
    });
  };

  const handleFilterChange = useCallback((filter: CommandCenterFilter) => {
    setVisibleHotspotIds(filter.visibleHotspotIds);
  }, []);

  // ── Derived ────────────────────────────────────────────────────────────
  const loadingOperations = loadingPredictions || loadingRecommendations;

  const criticalHighCount = predictions.filter(
    (p) => p.risk_level === 'Critical' || p.risk_level === 'High',
  ).length;

  const sortOptions = SORT_OPTIONS[activeTab];

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <div className="command-shell relative flex h-screen w-screen flex-col overflow-hidden bg-[#070b16] font-sans">

      {/* ════════════════════════════════════════════════════════════════
          TOP HEADER — logo · search · filter chips · sort · theme toggle
         ════════════════════════════════════════════════════════════════ */}
      <header className="command-header z-20 flex min-h-[56px] shrink-0 items-center gap-3 border-b border-white/8 px-4 py-2 md:px-5">

        {/* Logo */}
        <div className="flex shrink-0 items-center gap-2.5">
          <div className="rounded-lg border border-brand-teal/20 bg-brand-teal/10 p-2">
            <Compass className="h-4 w-4 text-brand-teal" />
          </div>
          <div className="hidden lg:block">
            <p className="text-sm font-semibold tracking-wide text-white leading-tight">
              Bengaluru Traffic Command
            </p>
            <p className="text-[10px] text-slate-500 leading-tight">
              AI parking intelligence
            </p>
          </div>
        </div>

        <span className="hidden lg:block mx-1 h-6 w-px bg-white/10 shrink-0" />

        {/* ── Search + filter chips + sort — takes remaining space ── */}
        <div className="flex flex-1 items-center gap-2 min-w-0">

          {/* Search input */}
          <div className="relative flex-1 min-w-0">
            <input
              type="text"
              placeholder={
                activeTab === 'deployments'
                  ? 'Search deployments, priorities, windows…'
                  : 'Search zones, IDs, locations…'
              }
              value={rawSearch}
              onChange={(e) => setRawSearch(e.target.value)}
              className="w-full rounded-xl border-2 border-brand-teal/30 bg-[#0d1627] py-2 pl-9 pr-8 text-sm font-medium text-white placeholder-slate-500 shadow-md shadow-brand-teal/5 transition focus:border-brand-teal focus:outline-none"
            />
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-brand-teal/60 pointer-events-none" />
            {rawSearch && (
              <>
                <button
                  type="button"
                  onClick={() => setRawSearch('')}
                  className="absolute right-2.5 top-2.5 text-slate-400 hover:text-white transition"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </>
            )}
          </div>

          {/* Severity filter chips */}
          <div className="hidden items-center gap-1 md:flex shrink-0">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setSeverityFilter(f)}
                className={`rounded-lg border px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider transition ${
                  severityFilter === f
                    ? 'border-brand-teal/40 bg-brand-teal/20 text-brand-teal'
                    : 'border-white/8 bg-white/[0.03] text-slate-400 hover:border-white/20 hover:text-slate-200'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          {/* Sort selector — options change with active tab */}
          <div className="relative shrink-0">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="appearance-none rounded-lg border border-white/10 bg-[#0d1627] py-1.5 pl-2.5 pr-7 text-[10px] font-semibold uppercase tracking-wider text-slate-300 transition focus:border-brand-teal focus:outline-none cursor-pointer"
            >
              {sortOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <ArrowUpDown className="pointer-events-none absolute right-2 top-2 h-3 w-3 text-slate-400" />
          </div>
        </div>

        {/* Theme toggle removed */}
      </header>

      {/* ════════════════════════════════════════════════════════════════
          SUB-STRIP — stats + top-5 risk outlook
         ════════════════════════════════════════════════════════════════ */}
      <div className="z-10 flex shrink-0 items-center gap-0 border-b border-white/8 bg-[#080e1c] px-4 py-0 md:px-5 overflow-x-auto no-scrollbar">

        {/* Stat pills */}
        {[
          {
            label: 'Violations',
            value: loadingSummary ? '—' : (summary?.total_violations?.toLocaleString() ?? '—'),
            color: 'text-white',
          },
          {
            label: 'Hotspots',
            value: loadingSummary ? '—' : (summary?.total_hotspots?.toLocaleString() ?? '—'),
            color: 'text-white',
          },
          {
            label: 'Tmr Crit/High',
            value: loadingOperations ? '—' : String(criticalHighCount),
            color: criticalHighCount > 0 ? 'text-severity-critical' : 'text-white',
          },
        ].map((stat, i) => (
          <div key={stat.label} className="flex shrink-0 items-center">
            {i > 0 && <span className="mx-3 h-4 w-px bg-white/10" />}
            <div className="py-2.5">
              <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-slate-500 leading-none">
                {stat.label}
              </p>
              <p className={`mt-0.5 text-sm font-bold tabular-nums leading-none ${stat.color}`}>
                {stat.value}
              </p>
            </div>
          </div>
        ))}

        {/* Divider before risk outlook */}
        {!loadingPredictions && predictions.length > 0 && (
          <span className="mx-4 h-4 w-px shrink-0 bg-white/10" />
        )}

        {/* Top-5 Risk Outlook */}
        {!loadingPredictions && predictions.length > 0 && (
          <div className="flex shrink-0 items-center gap-3 py-2">
            <span className="text-[9px] font-semibold uppercase tracking-[0.16em] text-slate-500 shrink-0">
              Top Risk
            </span>
            {predictions.slice(0, 5).map((pred) => {
              const risk = pred.risk_level.toLowerCase();
              const dot =
                risk === 'critical' ? 'bg-severity-critical' :
                risk === 'high'     ? 'bg-severity-high'     :
                risk === 'medium'   ? 'bg-severity-medium'   :
                                      'bg-severity-low';
              return (
                <button
                  key={pred.hotspot_id}
                  type="button"
                  onClick={() => {
                    const h = hotspots.find((x) => x.id === pred.hotspot_id);
                    if (h) handleSelectHotspot(h);
                  }}
                  className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] text-slate-300 transition hover:bg-white/[0.05] hover:text-white"
                  title={`${pred.hotspot_name} — Risk ${pred.risk_score}`}
                >
                  <span className={`h-2 w-2 shrink-0 rounded-full ${dot}`} />
                  <span className="max-w-[90px] truncate">{pred.hotspot_name}</span>
                  <span className="font-bold tabular-nums text-white">{pred.risk_score}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* ════════════════════════════════════════════════════════════════
          MAIN CONTENT ROW
         ════════════════════════════════════════════════════════════════ */}
      <div className="flex min-h-0 flex-1 flex-col lg:flex-row">

        {/* Command Center (left panel) */}
        <div className="order-2 max-h-[36vh] shrink-0 lg:order-none lg:max-h-none lg:h-full">
            <CommandCenter
              hotspots={hotspots}
              predictions={predictions}
              recommendations={recommendations}
              selectedHotspotId={selectedItem?.source === 'hotspot' ? selectedItem.hotspot?.id ?? null : null}
              selectedDeploymentId={selectedItem?.source === 'deployment' ? selectedItem.prediction?.hotspot_id ?? null : null}
              onSelectHotspot={handleSelectHotspot}
              onSelectDeployment={handleSelectDeployment}
              onFilterChange={handleFilterChange}
              loadingHotspots={loadingHotspots}
              loadingOperations={loadingOperations}
              // lifted state passed down
              activeTab={activeTab}
              onTabChange={handleTabChange}
              search={search}
              severityFilter={severityFilter}
              sortBy={sortBy}
              piiThresholds={piiThresholds}
            />
        </div>

        {/* Map — always mounted so MapLibre gets a stable container before data arrives */}
        <div className="order-1 min-h-[54vh] flex-1 lg:order-none lg:min-h-0">
          <main className="relative h-full min-h-[400px] p-2 lg:p-3">
            {loadingHotspots && (
              <div className="absolute inset-0 z-20 flex items-center justify-center bg-[#070b16]/60 text-slate-400 pointer-events-none">
                Loading hotspots...
              </div>
            )}
            {!loadingHotspots && hotspots.length === 0 && (
              <div className="absolute inset-0 z-20 flex items-center justify-center text-slate-400 pointer-events-none">
                No hotspots found
              </div>
            )}
            {!loadingHotspots && hotspots.length > 0 && (
              <div className="absolute top-4 right-4 z-10 rounded bg-black/50 px-3 py-1 text-xs text-white">
                {hotspots.length} hotspots loaded
              </div>
            )}
            <HotspotMap
              hotspots={hotspots}
              selectedHotspot={selectedItem?.hotspot || null}
              predictions={predictions}
              onSelect={handleSelectHotspot}
              onDeselect={() => setSelectedItem(null)}
              visibleHotspotIds={visibleHotspotIds}
              colorBy={activeTab === 'deployments' ? 'risk' : 'pii'}
              piiThresholds={piiThresholds}
            />
          </main>
        </div>

        {/* Details panel */}
        {selectedItem && (
          <div className="order-3 shrink-0 lg:order-none lg:h-full">
            <HotspotDetailsPanel
              hotspot={selectedItem.hotspot}
              prediction={selectedItem.prediction}
              recommendation={selectedItem.recommendation}
              onClose={() => setSelectedItem(null)}
            />
          </div>
        )}
      </div>
    </div>
  );
};
