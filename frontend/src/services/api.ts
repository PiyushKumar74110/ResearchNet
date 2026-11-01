import type { ResearchEvent, ResearchJob } from "../types/research";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

async function parseError(response: Response): Promise<Error> {
  const body = await response.json().catch(() => ({}));
  return new Error(body.detail ?? body.message ?? `Request failed (${response.status})`);
}

export async function startResearch(topic: string): Promise<{ job_id: string; status: string }> {
  const response = await fetch(`${API_BASE}/api/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic }),
  });
  if (!response.ok) throw await parseError(response);
  return response.json();
}

export async function getResearch(jobId: string): Promise<ResearchJob> {
  const response = await fetch(`${API_BASE}/api/research/${encodeURIComponent(jobId)}`);
  if (!response.ok) throw await parseError(response);
  return response.json();
}

export function subscribeToResearch(
  jobId: string,
  onEvent: (event: ResearchEvent) => void,
  onError: (error: Error) => void,
): () => void {
  const source = new EventSource(`${API_BASE}/api/research/${encodeURIComponent(jobId)}/events`);
  source.onmessage = (message: MessageEvent<string>) => {
    try {
      const event = JSON.parse(message.data) as ResearchEvent;
      onEvent(event);
      if (event.type === "completed" || event.type === "failed") source.close();
    } catch {
      onError(new Error("Received an invalid progress event from the backend."));
      source.close();
    }
  };
  source.onerror = () => {
    if (source.readyState === EventSource.CLOSED) {
      onError(new Error("The progress connection closed. Check the job status or backend logs."));
    }
  };
  return () => source.close();
}

export { API_BASE };
