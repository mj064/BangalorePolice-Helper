export interface RiskAppearance {
  text: string;
  bg: string;
  textCol: string;
  border: string;
  accent: string;
}

export const getRiskAppearanceFromScore = (score: number): RiskAppearance => {
  if (score >= 66) {
    return {
      text: 'Critical',
      bg: 'bg-severity-critical/15',
      textCol: 'text-severity-critical',
      border: 'border-severity-critical/30',
      accent: 'bg-severity-critical',
    };
  }

  if (score >= 56) {
    return {
      text: 'High',
      bg: 'bg-severity-high/15',
      textCol: 'text-severity-high',
      border: 'border-severity-high/30',
      accent: 'bg-severity-high',
    };
  }

  if (score >= 46) {
    return {
      text: 'Medium',
      bg: 'bg-severity-medium/15',
      textCol: 'text-severity-medium',
      border: 'border-severity-medium/30',
      accent: 'bg-severity-medium',
    };
  }

  return {
    text: 'Low',
    bg: 'bg-severity-low/15',
    textCol: 'text-severity-low',
    border: 'border-severity-low/30',
    accent: 'bg-severity-low',
  };
};

export const getRiskAppearanceFromLevel = (riskLevel: string): RiskAppearance => {
  const normalized = riskLevel.trim().toLowerCase();

  if (normalized === 'critical') {
    return getRiskAppearanceFromScore(100);
  }

  if (normalized === 'high') {
    return getRiskAppearanceFromScore(70);
  }

  if (normalized === 'medium') {
    return getRiskAppearanceFromScore(45);
  }

  return getRiskAppearanceFromScore(15);
};

export interface TrendAppearance {
  label: string;
  delta: number;
  textCol: string;
}

export const getPredictionTrend = (
  currentImpactScore: number | null,
  tomorrowRiskScore: number
): TrendAppearance => {
  if (currentImpactScore === null) {
    return {
      label: 'Forecast only',
      delta: tomorrowRiskScore,
      textCol: 'text-slate-300',
    };
  }

  const delta = tomorrowRiskScore - currentImpactScore;

  if (delta >= 10) {
    return { label: 'Escalating', delta, textCol: 'text-severity-critical' };
  }

  if (delta <= -10) {
    return { label: 'Cooling', delta, textCol: 'text-severity-low' };
  }

  return { label: 'Stable Outlook', delta, textCol: 'text-severity-medium' };
};
