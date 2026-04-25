"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Gavel, Plus, FileText, Send, CheckCircle, Clock, Loader2,
  ExternalLink, ChevronDown, ChevronUp, Copy
} from "lucide-react";
import toast from "react-hot-toast";
import { enforcementAPI, detectionsAPI } from "@/lib/api";

const STATUS_CONFIG: Record<string, { label: string; cls: string }> = {
  draft: { label: "Draft", cls: "badge-info" },
  sent: { label: "Sent", cls: "badge-warning" },
  acknowledged: { label: "Acknowledged", cls: "badge-success" },
  resolved: { label: "Resolved", cls: "badge-success" },
  escalated: { label: "Escalated", cls: "badge-critical" },
};

export default function EnforcementPage() {
  const [cases, setCases] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [expandedCase, setExpandedCase] = useState<number | null>(null);
  const [noticeContent, setNoticeContent] = useState<Record<number, string>>({});
  const [stats, setStats] = useState<any>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [caseRes, statRes] = await Promise.all([
        enforcementAPI.listCases({ limit: 50 }),
        enforcementAPI.stats(),
      ]);
      setCases(caseRes.data.cases);
      setTotal(caseRes.data.total);
      setStats(statRes.data);
    } catch {
      toast.error("Failed to load enforcement cases");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleViewNotice = async (caseId: number) => {
    if (noticeContent[caseId]) {
      setExpandedCase(expandedCase === caseId ? null : caseId);
      return;
    }
    try {
      const res = await enforcementAPI.getNotice(caseId);
      setNoticeContent((n) => ({ ...n, [caseId]: res.data.notice }));
      setExpandedCase(caseId);
    } catch {
      toast.error("Failed to generate notice");
    }
  };

  const handleSendNotice = async (caseId: number) => {
    try {
      await enforcementAPI.sendNotice(caseId);
      setCases((c) => c.map((x) => x.id === caseId ? { ...x, status: "sent" } : x));
      toast.success("✅ Notice marked as sent");
    } catch {
      toast.error("Failed to send notice");
    }
  };

  const handleResolve = async (caseId: number) => {
    try {
      await enforcementAPI.updateCase(caseId, { status: "resolved", resolution_notes: "Content removed by infringer" });
      setCases((c) => c.map((x) => x.id === caseId ? { ...x, status: "resolved" } : x));
      toast.success("Case resolved!");
    } catch {
      toast.error("Update failed");
    }
  };

  const copyNotice = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Notice copied to clipboard");
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-black mb-1">
            <span className="gradient-text">Enforcement Center</span>
          </h1>
          <p className="text-slate-400">Manage DMCA notices and legal actions</p>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total Cases", value: stats.total_cases, color: "text-indigo-400" },
            { label: "Notices Sent", value: stats.sent, color: "text-amber-400" },
            { label: "Resolved", value: stats.resolved, color: "text-emerald-400" },
            { label: "Resolution Rate", value: `${stats.resolution_rate}%`, color: "text-purple-400" },
          ].map(({ label, value, color }) => (
            <div key={label} className="stat-card text-center">
              <div className={`text-3xl font-black ${color} mb-1`}>{value}</div>
              <div className="text-sm text-slate-400">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tip */}
      <div className="glass-light border border-indigo-500/20 rounded-xl p-4 mb-6 text-sm text-slate-400 flex items-start gap-3">
        <Gavel className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
        <p>
          To create a case, go to the <strong className="text-indigo-300">Detections</strong> page and click the
          ⚖️ icon on any active detection. Cases will appear here with auto-generated legal notices.
        </p>
      </div>

      {/* Cases */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
          </div>
        ) : cases.length === 0 ? (
          <div className="glass text-center py-20">
            <Gavel className="w-16 h-16 text-slate-700 mx-auto mb-4" />
            <p className="text-lg font-semibold text-slate-400">No enforcement cases yet</p>
            <p className="text-slate-500 text-sm mt-2">
              Create a case from the Detections page when you find an infringement
            </p>
          </div>
        ) : (
          cases.map((c) => {
            const st = STATUS_CONFIG[c.status] || STATUS_CONFIG.draft;
            const isExpanded = expandedCase === c.id;
            return (
              <motion.div
                key={c.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass overflow-hidden"
              >
                {/* Case Header */}
                <div className="p-5 flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center flex-shrink-0">
                    <Gavel className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="font-bold text-slate-200 font-mono text-sm">{c.case_number}</span>
                      <span className={`badge ${st.cls}`}>{st.label}</span>
                      <span className="badge badge-info">{c.case_type.toUpperCase()}</span>
                    </div>
                    {c.detection_url && (
                      <a
                        href={c.detection_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 mt-1 truncate max-w-lg"
                      >
                        {c.platform && `[${c.platform}] `}{c.detection_url.slice(0, 80)}...
                        <ExternalLink className="w-3 h-3 flex-shrink-0" />
                      </a>
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {c.status === "draft" && (
                      <button
                        onClick={() => handleSendNotice(c.id)}
                        className="btn-primary py-1.5 px-3 text-xs"
                      >
                        <Send className="w-3 h-3" /> Send Notice
                      </button>
                    )}
                    {c.status === "sent" && (
                      <button
                        onClick={() => handleResolve(c.id)}
                        className="btn-secondary py-1.5 px-3 text-xs text-emerald-400"
                      >
                        <CheckCircle className="w-3 h-3" /> Mark Resolved
                      </button>
                    )}
                    <button
                      onClick={() => handleViewNotice(c.id)}
                      className="btn-secondary py-1.5 px-3 text-xs gap-1"
                    >
                      <FileText className="w-3 h-3" />
                      {isExpanded ? "Hide" : "View"} Notice
                      {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>
                  </div>
                </div>

                {/* Notice Content */}
                {isExpanded && noticeContent[c.id] && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-t border-white/5"
                  >
                    <div className="p-5">
                      <div className="flex justify-between items-center mb-3">
                        <h3 className="text-sm font-bold text-slate-300">Legal Notice Content</h3>
                        <button
                          onClick={() => copyNotice(noticeContent[c.id])}
                          className="btn-secondary py-1 px-3 text-xs"
                        >
                          <Copy className="w-3 h-3" /> Copy
                        </button>
                      </div>
                      <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap bg-black/30 rounded-xl p-4 max-h-64 overflow-y-auto leading-relaxed">
                        {noticeContent[c.id]}
                      </pre>
                    </div>
                  </motion.div>
                )}

                {/* Timestamps */}
                <div className="px-5 pb-4 flex gap-4 text-xs text-slate-600">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Created: {new Date(c.created_at).toLocaleString()}
                  </span>
                  {c.notice_sent_at && (
                    <span className="flex items-center gap-1">
                      <Send className="w-3 h-3" />
                      Sent: {new Date(c.notice_sent_at).toLocaleString()}
                    </span>
                  )}
                  {c.resolved_at && (
                    <span className="flex items-center gap-1 text-emerald-600">
                      <CheckCircle className="w-3 h-3" />
                      Resolved: {new Date(c.resolved_at).toLocaleString()}
                    </span>
                  )}
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}
