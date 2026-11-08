import {
  CampaignSummaryListSchema,
  CampaignSummarySchema,
  CreateCampaignRequestSchema,
  CreateCampaignResponseSchema,
  VersionDiffSchema,
  VersionSummaryListSchema,
  type CampaignSummary,
  type CreateCampaignResponse,
  type VersionDiff,
  type VersionSummary,
} from "@/lib/schemas";
import { CampaignPackageSchema, type CampaignPackage } from "@/lib/schemas";
import { apiRequest } from "./client";

function campaignPath(id: string): string {
  return `/campaigns/${encodeURIComponent(id)}`;
}

export function listCampaigns(signal?: AbortSignal): Promise<CampaignSummary[]> {
  return apiRequest("/campaigns", CampaignSummaryListSchema, { signal });
}

export function getCampaign(id: string, signal?: AbortSignal): Promise<CampaignSummary> {
  return apiRequest(campaignPath(id), CampaignSummarySchema, { signal });
}

export async function createCampaign(idea: string): Promise<CreateCampaignResponse> {
  const body = CreateCampaignRequestSchema.parse({ idea });
  return apiRequest("/campaigns", CreateCampaignResponseSchema, { method: "POST", body });
}

export function listVersions(id: string, signal?: AbortSignal): Promise<VersionSummary[]> {
  return apiRequest(`${campaignPath(id)}/versions`, VersionSummaryListSchema, { signal });
}

export function getVersion(
  id: string,
  version: number,
  signal?: AbortSignal,
): Promise<CampaignPackage> {
  return apiRequest(`${campaignPath(id)}/versions/${version}`, CampaignPackageSchema, { signal });
}

export function getVersionDiff(
  id: string,
  from: number,
  to: number,
  signal?: AbortSignal,
): Promise<VersionDiff> {
  return apiRequest(`${campaignPath(id)}/versions/${from}/diff/${to}`, VersionDiffSchema, {
    signal,
  });
}
