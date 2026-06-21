import { Prediction, Recommendation } from '../services/api';

export interface DeploymentAction {
  hotspot_id: string;
  hotspot_name: string;
  priority: string;
  risk_score: number;
  risk_level: string;
  prediction_horizon: string;
  officers: number;
  tow_vehicles: number;
  deployment_window: string;
  reason: string;
}

const PRIORITY_RANK: Record<string, number> = {
  Critical: 4,
  High: 3,
  Medium: 2,
  Low: 1,
};

export const mergePredictionsAndRecommendations = (
  predictions: Prediction[],
  recommendations: Recommendation[],
): DeploymentAction[] => {
  const recommendationsByHotspot = new Map(
    recommendations.map((recommendation) => [recommendation.hotspot_id, recommendation]),
  );

  return predictions
    .map((prediction) => {
      const recommendation = recommendationsByHotspot.get(prediction.hotspot_id);
      if (!recommendation) {
        return null;
      }

      return {
        hotspot_id: prediction.hotspot_id,
        hotspot_name: prediction.hotspot_name,
        priority: recommendation.priority,
        risk_score: prediction.risk_score,
        risk_level: prediction.risk_level,
        prediction_horizon: prediction.prediction_horizon,
        officers: recommendation.officers,
        tow_vehicles: recommendation.tow_vehicles,
        deployment_window: recommendation.deployment_window,
        reason: recommendation.reason,
      };
    })
    .filter((action): action is DeploymentAction => action !== null)
    .sort((left, right) => {
      const priorityDelta =
        (PRIORITY_RANK[right.priority] ?? 0) - (PRIORITY_RANK[left.priority] ?? 0);
      if (priorityDelta !== 0) {
        return priorityDelta;
      }
      return right.risk_score - left.risk_score;
    });
};

export const getTopPriorityDeployments = (
  actions: DeploymentAction[],
  limit = 5,
): DeploymentAction[] => actions.slice(0, limit);
