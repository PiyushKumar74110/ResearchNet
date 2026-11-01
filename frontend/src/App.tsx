import { useCallback, useEffect, useRef, useState } from "react";
import { Activity, ArrowUpRight, BookOpen, CheckCircle2, FlaskConical, Microscope, Search, Sparkles, TriangleAlert } from "lucide-react";
import StageList from "./components/StageList";
import ReportPanel from "./components/ReportPanel";
import { getResearch, startResearch, subscribeToResearch } from "./services/api";
import type { ResearchEvent, ResearchJob, StageName, StageStatus } from "./types/research";

const initialStatuses: Record<StageName, StageStatus> = {
  search: "waiting", reader: "waiting", writer: "waiting", critic: "waiting",
};
const examples = ["Time-series foundation models", "CRISPR gene editing", "Fusion energy progress"];

export default function App() {
  const [topic, setTopic] = useState("");
  const [job, setJob] = useState<ResearchJob | null>(null);
  const [statuses, setStatuses] = useState(initialStatuses);
  const [currentStage, setCurrentStage] = useState("Ready for your next research question");
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState("");
  const unsubscribe = useRef<(() => void) | null>(null);

  useEffect(() => () => unsubscribe.current?.(), []);

  const applyJob = useCallback((next: ResearchJob) => {
    setJob(next);
    if (next.status === "completed") setCurrentStage("Research pipeline completed");
    if (next.status === "failed") setCurrentStage("Pipeline stopped with an error");
  }, []);

  const handleEvent = useCallback((event: ResearchEvent) => {
    if (event.type === "snapshot" && event.job) {
      applyJob(event.job);
      const results = event.job.results;
      setStatuses({
        search: results.search ? "completed" : "waiting",
        reader: results.reader ? "completed" : "waiting",
        writer: results.writer ? "completed" : "waiting",
        critic: results.critic ? "completed" : "waiting",
      });
      return;
    }
    if (event.type === "stage" && event.stage && event.status) {
      setStatuses((previous) => ({ ...previous, [event.stage!]: event.status! }));
      if (event.status === "running") setCurrentStage(event.message ?? `Running ${event.stage}`);
      if (event.status === "completed" && event.result) {
        setJob((previous) => previous ? {
          ...previous,
          results: { ...previous.results, [event.stage!]: event.result },
        } : previous);
      }
    }
    if (event.type === "completed" && event.job) {
      applyJob(event.job);
      setStatuses({ search: "completed", reader: "completed", writer: "completed", critic: "completed" });
    }
    if (event.type === "failed" && event.job) {
      applyJob(event.job);
      setError(event.message ?? event.job.error ?? "Research failed. Check your API keys and backend logs.");
    }
  }, [applyJob]);

  const runResearch = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanedTopic = topic.trim();
    if (cleanedTopic.length < 3) {
      setError("Enter a research topic with at least 3 characters.");
      return;
    }
    unsubscribe.current?.();
    setError("");
    setIsStarting(true);
    setJob(null);
    setStatuses({ ...initialStatuses });
    setCurrentStage("Creating your research job…");
    try {
      const response = await startResearch(cleanedTopic);
      const initialJob = await getResearch(response.job_id);
      applyJob(initialJob);
      unsubscribe.current = subscribeToResearch(response.job_id, handleEvent, (nextError) => setError(nextError.message));
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Could not start research.");
    } finally {
      setIsStarting(false);
    }
  };

  const isRunning = isStarting || job?.status === "queued" || job?.status === "running";
  const hasReport = Boolean(job?.results.writer);
  const copyTopic = (value: string) => setTopic(value);

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#" aria-label="ResearchMind home">
          <div className="brand-mark"><Microscope size={20} /></div>
          <span>research<span className="brand-accent">mind</span></span>
        </a>
        <div className="topbar-right"><span className="system-indicator" /><span>RESEARCH SYSTEM</span><span className="version">V1.0</span></div>
      </header>

      <main className="main-layout">
        <section className="hero">
          <div className="hero-badge"><Sparkles size={13} /> MULTI-AGENT RESEARCH WORKSPACE</div>
          <h1>Think deeper.<br /><span>Find the signal.</span></h1>
          <p className="hero-description">A team of AI agents searches, reads, writes, and critiques — turning a research question into a structured report.</p>
        </section>

        <section className="workspace-grid">
          <div className="left-column">
            <form className="topic-card" onSubmit={runResearch}>
              <label htmlFor="topic">Your research question</label>
              <div className="topic-input-wrap"><Search size={18} /><input id="topic" value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="e.g. How are time-series foundation models evaluated?" maxLength={500} disabled={Boolean(isRunning)} /></div>
              <div className="topic-meta"><span>Be specific for more useful findings.</span><span>{topic.length}/500</span></div>
              <button className="primary-button" type="submit" disabled={Boolean(isRunning) || topic.trim().length < 3}>
                {isRunning ? <><span className="button-spinner" /> Research in progress</> : <><Sparkles size={16} /> Run research pipeline <ArrowUpRight size={16} /></>}
              </button>
            </form>

            <div className="examples-block">
              <div className="section-label">START WITH AN EXAMPLE</div>
              <div className="example-list">{examples.map((example) => <button className="example-chip" key={example} onClick={() => copyTopic(example)} disabled={Boolean(isRunning)}>{example}<ArrowUpRight size={12} /></button>)}</div>
            </div>

            {error && <div className="error-banner"><TriangleAlert size={17} /><span>{error}</span></div>}

            <div className="info-card">
              <div className="info-icon"><BookOpen size={18} /></div>
              <div><h3>Research, not just summaries</h3><p>The pipeline combines search snippets with deeper source reading, then asks a separate critic to identify gaps and weaknesses.</p></div>
            </div>
          </div>

          <aside className="pipeline-card">
            <div className="pipeline-header"><div><div className="eyebrow">WORKFLOW / LIVE</div><h2>Research pipeline</h2></div><div className={`live-badge ${isRunning ? "active" : ""}`}><span />{isRunning ? "ACTIVE" : job?.status === "completed" ? "COMPLETE" : "IDLE"}</div></div>
            <StageList statuses={statuses} currentStage={currentStage} />
            <div className="pipeline-bottom"><Activity size={15} /><span>Four focused stages · One report</span><span className="pipeline-count">04</span></div>
          </aside>
        </section>

        {job && (job.status === "completed" || hasReport || job.results.critic) && (
          <section className="results-section">
            <div className="results-heading"><div><div className="eyebrow">RESEARCH OUTPUT</div><h2>Findings & evaluation</h2></div><div className="result-topic"><CheckCircle2 size={15} /> {job.topic}</div></div>
            {hasReport && <ReportPanel report={job.results.writer!} topic={job.topic} />}
            {job.results.critic && <section className="content-panel critic-panel"><div className="panel-heading"><div className="panel-heading-icon green"><CheckCircle2 size={18} /></div><div><div className="eyebrow">OUTPUT / 02</div><h2>Critic review</h2></div></div><div className="critic-content">{job.results.critic}</div></section>}
            <div className="raw-grid">
              {job.results.search && <details className="raw-panel"><summary><Search size={15} /> Search results <span>RAW OUTPUT</span></summary><pre>{job.results.search}</pre></details>}
              {job.results.reader && <details className="raw-panel"><summary><BookOpen size={15} /> Source reading <span>RAW OUTPUT</span></summary><pre>{job.results.reader}</pre></details>}
            </div>
          </section>
        )}

        <footer className="footer"><div className="footer-brand"><FlaskConical size={15} /> RESEARCHMIND</div><span>Powered by LangChain · FastAPI · React</span><span>Verify important claims against original sources.</span></footer>
      </main>
    </div>
  );
}
