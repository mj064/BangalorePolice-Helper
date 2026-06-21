import React, { useEffect, useState } from 'react';
import { X, TrendingUp, TrendingDown, ArrowRight, BarChart3, Clock, Car } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, LineChart, Line } from 'recharts';
import { apiService, Hotspot, HotspotDetail, Prediction, Recommendation } from '../services/api';
import { getRiskAppearanceFromLevel, getRiskAppearanceFromScore } from '../utils/risk';
import { AnalyticsAccordion } from './AnalyticsAccordion';

interface HotspotDetailsPanelProps {
  hotspot: Hotspot | null;
  prediction?: Prediction | null;
  recommendation?: Recommendation | null;
  onClose: () => void;
}

type Tab = 'TODAY' | 'TOMORROW' | 'ANALYTICS';

export const HotspotDetailsPanel: React.FC<HotspotDetailsPanelProps> = ({
  hotspot,
  prediction = null,
  recommendation = null,
  onClose,
}) => {
  const [details, setDetails] = useState<HotspotDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('TODAY');

  useEffect(() => {
    if (!hotspot) {
      setDetails(null);
      setLoading(false);
      setError(null);
      return;
    }

    const fetchDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await apiService.getHotspot(hotspot.id);
        setDetails(data);
      } catch (err) {
        console.error("Failed to load hotspot details:", err);
        setError("Could not fetch detailed metrics.");
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [hotspot]);

  // Reset tab when selection changes, but prioritizing TOMORROW if clicked from deployments
  useEffect(() => {
    if (recommendation) {
      setActiveTab('TOMORROW');
    } else {
      setActiveTab('TODAY');
    }
  }, [hotspot, recommendation]);

  if (!hotspot && !prediction) return null;

  const getTrendIcon = (trend: string) => {
    if (trend === 'increasing') return <TrendingUp className="w-4 h-4 text-severity-critical mr-1" />;
    if (trend === 'decreasing') return <TrendingDown className="w-4 h-4 text-severity-low mr-1" />;
    return <ArrowRight className="w-4 h-4 text-slate-400 mr-1" />;
  };

  const displayName = hotspot?.name || prediction?.hotspot_name || 'Forecast Zone';
  const tomorrowRiskScore = prediction?.risk_score ?? null;
  const sev = hotspot ? getRiskAppearanceFromScore(hotspot.impact_score) : null;
  const predictionSeverity = prediction ? getRiskAppearanceFromLevel(prediction.risk_level) : null;

  const vehicleChartData = details 
    ? Object.entries(details.vehicle_distribution).slice(0, 5).map(([name, count]) => ({ name, count })) 
    : [];

  const hourlyChartData = details
    ? Object.entries(details.hourly_distribution).map(([hour, count]) => ({
        hour: `${hour.padStart(2, '0')}:00`,
        count
      }))
    : [];

  return (
    <div className="flex h-full w-full flex-col overflow-hidden border-t border-white/8 bg-[#0a1020]/98 lg:w-[360px] lg:border-l lg:border-t-0 shadow-2xl">
      <div className="flex items-center justify-between border-b border-white/8 px-5 py-4">
        <div className="min-w-0 pr-2">
          <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-teal">
            Zone Intelligence
          </span>
          <h2 className="truncate text-lg font-medium text-white mt-0.5" title={displayName}>
            {displayName}
          </h2>
        </div>
        <button 
          onClick={onClose}
          className="rounded-lg p-2 text-slate-400 transition hover:bg-white/10 hover:text-white shrink-0"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex border-b border-white/8">
        {(['TODAY', 'TOMORROW', 'ANALYTICS'] as Tab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-3 text-[11px] font-bold tracking-[0.1em] transition-colors ${
              activeTab === tab 
                ? 'text-brand-teal border-b-2 border-brand-teal bg-white/5' 
                : 'text-slate-500 hover:text-slate-300 hover:bg-white/[0.02]'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex flex-1 flex-col items-center justify-center text-slate-400">
          <div className="mb-3 h-8 w-8 animate-spin rounded-full border-4 border-brand-teal border-t-transparent" />
          <span className="text-sm font-medium tracking-wide">Loading intel...</span>
        </div>
      ) : (
        <div className="flex-1 space-y-5 overflow-y-auto p-5 scrollbar-thin">
          {error && (
            <div className="rounded-xl border border-severity-critical/20 bg-severity-critical/10 p-3 text-sm text-severity-critical">
              {error}
            </div>
          )}

          {activeTab === 'TODAY' && (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              {details && sev ? (
                <>
                  <div className={`rounded-xl border ${sev.border} bg-black/20 p-5 shadow-lg`}>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                          Classification
                        </span>
                        <span className={`mt-1.5 block text-2xl font-bold ${sev.textCol}`}>
                          {sev.text}
                        </span>
                        <div className="mt-2 flex items-center text-xs font-medium text-slate-300">
                          {getTrendIcon(details.trend)}
                          <span className="capitalize">{details.trend}</span>
                        </div>
                      </div>
                      <div className="rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3 text-center">
                        <span className="block text-[10px] uppercase tracking-wider text-slate-500">PII</span>
                        <span className="text-3xl font-bold text-white">{details.impact_score}</span>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/8 bg-black/20 p-5 shadow-lg">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                      Current Violations
                    </span>
                    <div className="mt-2 flex items-baseline gap-2">
                      <span className="text-3xl font-bold text-white">{details.violations}</span>
                      <span className="text-xs font-medium text-slate-400 tracking-wide uppercase">Recorded</span>
                    </div>
                  </div>
                </>
              ) : (
                <div className="rounded-xl border border-dashed border-white/10 bg-black/20 p-4 text-sm text-slate-400 text-center">
                  Zone metadata is unavailable for today's snapshot.
                </div>
              )}
            </div>
          )}

          {activeTab === 'TOMORROW' && (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              {prediction && predictionSeverity && tomorrowRiskScore !== null && (
                <div className={`rounded-xl border ${predictionSeverity.border} bg-black/20 p-5 shadow-lg`}>
                  <div className="mb-4 flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-brand-gold">
                        Prediction
                      </p>
                    </div>
                    <span className={`rounded-md px-2.5 py-1 text-[11px] font-bold tracking-wide ${predictionSeverity.bg} ${predictionSeverity.textCol}`}>
                      {prediction.risk_level}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500 block mb-1">
                      Forecast Score
                    </span>
                    <span className={`text-4xl font-bold ${predictionSeverity.textCol}`}>
                      {tomorrowRiskScore}
                    </span>
                  </div>
                </div>
              )}

              {recommendation ? (
                <div className="rounded-xl border border-brand-teal/30 bg-brand-teal/5 p-5 shadow-lg relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-brand-teal"></div>
                  <p className="mb-4 text-[10px] font-bold uppercase tracking-[0.16em] text-brand-teal">
                    Deployment Recommendation
                  </p>
                  
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="rounded-xl border border-brand-teal/10 bg-black/40 p-4">
                      <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-1.5 font-medium">Officers</p>
                      <p className="text-2xl font-bold text-white">{recommendation.officers}</p>
                    </div>
                    <div className="rounded-xl border border-brand-teal/10 bg-black/40 p-4">
                      <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-1.5 font-medium">Tow Vehicles</p>
                      <p className="text-2xl font-bold text-white">{recommendation.tow_vehicles}</p>
                    </div>
                  </div>
                  
                  <div className="rounded-xl border border-brand-teal/10 bg-black/40 p-4 mb-3">
                    <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-1.5 font-medium">Deployment Window</p>
                    <p className="text-base font-semibold tracking-wide text-white">{recommendation.deployment_window}</p>
                  </div>
                  
                  <div className="rounded-xl border border-brand-teal/10 bg-black/40 p-4">
                    <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-2 font-medium">Reasoning</p>
                    <p className="text-sm text-slate-300 leading-relaxed">{recommendation.reason}</p>
                  </div>
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-white/10 bg-black/20 p-4 text-sm text-slate-400 text-center">
                  No deployment recommendation generated for this zone.
                </div>
              )}
            </div>
          )}

          {activeTab === 'ANALYTICS' && (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              {details ? (
                <>
                  <AnalyticsAccordion
                    title="PII Component Breakdown"
                    icon={<BarChart3 className="h-4 w-4 text-brand-teal" />}
                  >
                    <div className="space-y-3 pt-1">
                      {[
                        { name: "Violation Density", val: details.violation_density, weight: "40%", color: "bg-brand-teal" },
                        { name: "Main Road Parking", val: details.main_road_score, weight: "30%", color: "bg-brand-gold" },
                        { name: "Peak Hour Violations", val: details.peak_hour_score, weight: "20%", color: "bg-severity-high" },
                        { name: "Repeat Violations", val: details.repeat_violation_score, weight: "10%", color: "bg-severity-critical" }
                      ].map((item) => (
                        <div key={item.name} className="space-y-1.5">
                          <div className="flex justify-between text-[11px]">
                            <span className="text-slate-300 font-medium">{item.name} <span className="text-[9px] text-slate-500 font-normal ml-1">({item.weight})</span></span>
                            <span className="font-bold text-white">{item.val.toFixed(0)}%</span>
                          </div>
                          <div className="h-2 overflow-hidden rounded-full border border-white/5 bg-black/50">
                            <div className={`h-full ${item.color} rounded-full`} style={{ width: `${item.val}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </AnalyticsAccordion>

                  <AnalyticsAccordion
                    title="Vehicle Distribution"
                    icon={<Car className="h-4 w-4 text-brand-teal" />}
                  >
                    <div className="h-36 pt-2">
                      {vehicleChartData.length === 0 ? (
                        <span className="text-xs text-slate-400">No data</span>
                      ) : (
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={vehicleChartData} layout="vertical" margin={{ left: -10, right: 10, top: 0, bottom: 0 }}>
                            <XAxis type="number" hide />
                            <YAxis dataKey="name" type="category" tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 500 }} width={80} />
                            <Tooltip 
                              contentStyle={{ background: '#0a1020', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', fontFamily: 'Outfit', borderRadius: '8px' }}
                              cursor={{fill: 'rgba(255,255,255,0.05)'}}
                            />
                            <Bar dataKey="count" fill="#5BC0BE" radius={[0, 4, 4, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      )}
                    </div>
                  </AnalyticsAccordion>

                  <AnalyticsAccordion
                    title="Hourly Distribution"
                    icon={<Clock className="h-4 w-4 text-brand-gold" />}
                  >
                    <div className="h-36 pt-2">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={hourlyChartData} margin={{ left: -25, right: 10, top: 5, bottom: 0 }}>
                          <XAxis dataKey="hour" tick={{ fill: '#94a3b8', fontSize: 9 }} tickMargin={8} />
                          <YAxis tick={{ fill: '#94a3b8', fontSize: 9 }} />
                          <Tooltip
                            contentStyle={{ background: '#0a1020', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', fontFamily: 'Outfit', borderRadius: '8px' }}
                          />
                          <Line type="monotone" dataKey="count" stroke="#FFD700" strokeWidth={2.5} dot={false} activeDot={{ r: 5, fill: '#FFD700', stroke: '#0a1020', strokeWidth: 2 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </AnalyticsAccordion>

                  <AnalyticsAccordion
                    title="Violation Categories"
                    icon={<BarChart3 className="h-4 w-4 text-severity-high" />}
                  >
                    <div className="space-y-2.5 pt-1">
                      {Object.entries(details.violation_type_distribution).slice(0, 5).map(([type, count]) => (
                        <div key={type} className="flex items-center justify-between text-xs border-b border-white/5 pb-2 last:border-0 last:pb-0">
                          <span className="max-w-[75%] truncate font-medium text-slate-300" title={type}>
                            {type}
                          </span>
                          <span className="rounded bg-white/5 px-2 py-1 font-bold text-slate-200">
                            {count}
                          </span>
                        </div>
                      ))}
                    </div>
                  </AnalyticsAccordion>
                </>
              ) : (
                <div className="rounded-xl border border-dashed border-white/10 bg-black/20 p-4 text-sm text-slate-400 text-center">
                  Analytics metadata is unavailable.
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
