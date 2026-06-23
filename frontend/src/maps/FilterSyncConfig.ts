/**
 * Proof-of-concept filter config that maps prediction risk_level
 * to the same categories used in CommandCenter, RiskUtils, and map legend.
 */
export const SEVERITY_CATEGORIES = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const;
export type SeverityCategory = typeof SEVERITY_CATEGORIES[number];

export const normalizeRiskLevel = (level: string): string => level.trim().toUpperCase();

export const riskLevelToCategory = (level: string): SeverityCategory => {
  const normalized = normalizeRiskLevel(level);
  if (normalized === 'CRITICAL') return 'CRITICAL';
  if (normalized === 'HIGH') return 'HIGH';
  if (normalized === 'MEDIUM') return 'MEDIUM';
  return 'LOW';
};