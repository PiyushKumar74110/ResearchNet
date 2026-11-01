import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Download, FileText } from "lucide-react";

interface ReportPanelProps {
  report: string;
  topic: string;
}

export default function ReportPanel({ report, topic }: ReportPanelProps) {
  const downloadReport = () => {
    const blob = new Blob([report], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `researchmind-${topic.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "report"}.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="content-panel report-panel">
      <div className="panel-heading">
        <div className="panel-heading-icon orange"><FileText size={18} /></div>
        <div><div className="eyebrow">OUTPUT / 01</div><h2>Research report</h2></div>
        <button className="secondary-button" onClick={downloadReport}><Download size={15} /> Export .md</button>
      </div>
      <article className="markdown-body"><ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown></article>
    </section>
  );
}
