import { Check, Circle, LoaderCircle, Search, BookOpen, FileText, ClipboardCheck } from "lucide-react";
import type { StageName, StageStatus } from "../types/research";

const stages: { id: StageName; title: string; description: string; Icon: typeof Search }[] = [
  { id: "search", title: "Search agent", description: "Finds relevant web sources", Icon: Search },
  { id: "reader", title: "Reader agent", description: "Extracts useful source content", Icon: BookOpen },
  { id: "writer", title: "Writer chain", description: "Builds a structured report", Icon: FileText },
  { id: "critic", title: "Critic chain", description: "Reviews quality and evidence", Icon: ClipboardCheck },
];

interface StageListProps {
  statuses: Record<StageName, StageStatus>;
  currentStage: string;
}

export default function StageList({ statuses, currentStage }: StageListProps) {
  return (
    <div className="stage-list">
      {stages.map(({ id, title, description, Icon }, index) => {
        const status = statuses[id];
        return (
          <div className={`stage-card ${status}`} key={id}>
            <div className="stage-icon">{status === "completed" ? <Check size={18} /> : status === "running" ? <LoaderCircle className="spin" size={18} /> : <Icon size={18} />}</div>
            <div className="stage-copy">
              <div className="stage-overline">STEP 0{index + 1}</div>
              <div className="stage-title">{title}</div>
              <div className="stage-description">{description}</div>
            </div>
            <span className={`status-pill ${status}`}>{status === "completed" ? "Done" : status === "running" ? "Running" : status === "failed" ? "Failed" : "Waiting"}</span>
          </div>
        );
      })}
      <div className="pipeline-footnote"><Circle size={7} fill="currentColor" /> {currentStage}</div>
    </div>
  );
}
