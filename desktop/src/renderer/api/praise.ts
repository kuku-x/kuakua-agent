import { getPraiseConfig, updatePraiseConfig, getMilestones, createMilestone, getProfiles, submitFeedback } from '@/api'
import type { PraiseConfig, MilestoneResponse, ProfileResponse, FeedbackCreate } from '@/types/api'

export const praiseApi = {
  getConfig: () => getPraiseConfig(),
  updateConfig: (data: PraiseConfig) => updatePraiseConfig(data),
  getMilestones: () => getMilestones(),
  createMilestone: (data: { event_type: string; title: string; description?: string }) =>
    createMilestone(data),
  getProfiles: () => getProfiles(),
  submitFeedback: (data: FeedbackCreate) => submitFeedback(data),
}

export type { PraiseConfig, MilestoneResponse, ProfileResponse, FeedbackCreate }
