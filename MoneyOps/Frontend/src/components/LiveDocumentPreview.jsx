import { FileText, Download, Sparkles } from "lucide-react";

export default function LiveDocumentPreview({ insight, onClose }) {
    if (!insight) return null;

    const suggestions = insight.matched_terms?.length
        ? [
            `Ask follow-up questions about ${insight.matched_terms[0]}`,
            "Try asking for dates, totals, clauses, or parties",
        ]
        : ["Ask for a summary, amount, due date, clause, or vendor details"];

    return (
        <div
            className="mt-4 rounded-xl border border-white/10 p-3"
            style={{ backgroundColor: "rgba(255,255,255,0.03)" }}
        >
            <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2 min-w-0">
                    <div
                        className="h-8 w-8 rounded-lg flex items-center justify-center shrink-0"
                        style={{ backgroundColor: "rgba(76,187,23,0.14)", color: "#4CBB17" }}
                    >
                        <FileText className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                        <p className="text-sm font-semibold text-white truncate">
                            {insight.document_name || insight.title || "Document Intelligence"}
                        </p>
                        <p className="text-[11px]" style={{ color: "rgba(255,255,255,0.45)" }}>
                            {insight.document_category || "Uploaded document"}
                        </p>
                    </div>
                </div>
                <button
                    type="button"
                    onClick={onClose}
                    className="text-[10px] px-2 py-1 rounded-md border border-white/10 text-white/55 hover:text-white hover:bg-white/5 transition-colors"
                >
                    Hide
                </button>
            </div>

            {insight.question && (
                <div className="mt-3 rounded-lg px-3 py-2 border border-white/5" style={{ backgroundColor: "rgba(255,255,255,0.02)" }}>
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: "rgba(255,255,255,0.3)" }}>
                        Your Question
                    </p>
                    <p className="text-xs mt-1 text-white/80">{insight.question}</p>
                </div>
            )}

            <div className="mt-3 rounded-lg px-3 py-2 border border-white/5" style={{ backgroundColor: "rgba(255,255,255,0.02)" }}>
                <div className="flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-[#4CBB17]" />
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: "rgba(255,255,255,0.3)" }}>
                        Answer
                    </p>
                </div>
                <p className="text-xs mt-1.5 leading-relaxed text-white/80">{insight.message}</p>
            </div>

            {insight.snippet && (
                <div className="mt-3 rounded-lg px-3 py-2 border border-white/5" style={{ backgroundColor: "rgba(255,255,255,0.02)" }}>
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: "rgba(255,255,255,0.3)" }}>
                        Source Extract
                    </p>
                    <p className="text-[11px] mt-1.5 leading-relaxed text-white/60">{insight.snippet}</p>
                </div>
            )}

            <div className="mt-3 flex items-center justify-between gap-3">
                <div className="min-w-0">
                    {suggestions.map((suggestion) => (
                        <p key={suggestion} className="text-[11px] text-white/45 truncate">
                            {suggestion}
                        </p>
                    ))}
                </div>
                {insight.download_url && (
                    <a
                        href={insight.download_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 text-[11px] px-2.5 py-1.5 rounded-lg border border-white/10 text-white/70 hover:text-white hover:bg-white/5 transition-colors shrink-0"
                    >
                        <Download className="h-3 w-3" />
                        Open
                    </a>
                )}
            </div>
        </div>
    );
}
