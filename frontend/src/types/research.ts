export type StageName = "search" | "reader" | "writer" | "critic";
export type StageStatus = "waiting" | "running" | "completed" | "failed";

export interface ResearchResults {
  search?: string;
  reader?: string;
  writer?: string;
  critic?: string;
}

export interface ResearchJob {
  job_id: string;
  topic: string;
  status: "queued" | "running" | "completed" | "failed";
  stage: string;
  results: ResearchResults;
  error: string | null;
}

export interface ResearchEvent {
  type: "snapshot" | "stage" | "completed" | "failed";
  stage?: StageName;
  status?: StageStatus;
  message?: string;
  result?: string;
  job?: ResearchJob;
}
