"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertTriangle, ExternalLink, Shield, Loader2, RefreshCw,
  Globe, Filter, Gavel, CheckCircle, Clock, Zap
} from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";
import { detectionsAPI, enforcementAPI, Detection } from "@/lib/api";

const SEVERITY_CONFIG = {
  critical: { label: "Critical", className: "badge-critical", color: "text-red-400" },
  high: { label: "High", className: "badge-danger", color: "text-orange-400" },
  medium: { label: "Medium", className: "badge-warning", color: "text-amber-400" },
  low: { label: "Low", className: "badge-info", color: "text-blue-400" },
};

const PLATFORM_ICONS: Record<string, string> = {
  youtube: "🎬",
  instagram: "📸",
  twitter: "🐦",
  facebook: "📘",
  tiktok: "🎵",
  reddit: "🔴",
  sports_site: "⚽",
  website: "🌐",
};

function SimilarityBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = pct >= 95 ? "#dc2626" : pct >= 85 ? "#f59e0b" : pct >= 65 ? "#6366f1" : "#10b981";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-xs font-semibold" style={{ color }}>{pct}%</span>
    </div>
  );
}

export default function DetectionsPage() {
  const [detections, setDetections] = useState<Detection[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterPlatform, setFilterPlatform] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await detectionsAPI.list({
        severity: filterSeverity || undefined,
        status: filterStatus || undefined,
        platform: filterPlatform || undefined,
        limit: 100,
      });
      setDetections(res.data.detections);
      setTotal(res.data.total);
    } catch {
      toast.error("Failed to load detections");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filterSeverity, filterStatus, filterPlatform]);

  const handleUpdateStatus = async (id: number, status: string) => {
    try {
      await detectionsAPI.update(id, { status });
      setDetections((d) => d.map((x) => x.id === id ? { ...x, status } : x));
      toast.success(`Detection marked as ${status}`);
    } catch {
      toast.error("Update failed");
    }
  };

  const handleCreateCase = async (detectionId: number) => {
    try {
      await enforcementAPI.createCase({ detection_id: detectionId, case_type: "dmca" });
      toast.success("DMCA case created! Check Enforcement tab.");
    } catch (err: any) {
      const msg = err.response?.data?.detail || "Case creation failed";
      toast.error(msg);
    }
  };

  const handleSeedDemo = async () => {
    setSeeding(true);
    try {
      await detectionsAPI.seedDemo();
      toast.success("Demo detections created!");
      load();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Seed failed — upload at least 1 asset first");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-black mb-1">
            <span className="gradient-text">Detections</span>
          </h1>
          <p className="text-slate-400">{total} infringement(s) found across the web</p>
        </div>
        <div className="flex gap-3">
          <button onClick={handleSeedDemo} disabled={seeding} className="btn-secondary py-2 px-4 text-sm">
            {seeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            Seed Demo Data
          </button>
          <button onClick={load} className="btn-secondary py-2 px-4 text-sm">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select className="form-input py-2.5 w-auto" value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)}>
          <option value="" style={{ background: "#0d0d1f" }}>All Severities</option>
          {["critical", "high", "medium", "low"].map((s) => (
            <option key={s} value={s} style={{ background: "#0d0d1f" }}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>
        <select className="form-input py-2.5 w-auto" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="" style={{ background: "#0d0d1f" }}>All Statuses</option>
          {["active", "resolved", "false_positive", "dmca_sent"].map((s) => (
            <option key={s} value={s} style={{ background: "#0d0d1f" }}>{s.replace("_", " ")}</option>
          ))}
        </select>
        <select className="form-input py-2.5 w-auto" value={filterPlatform} onChange={(e) => setFilterPlatform(e.target.value)}>
          <option value="" style={{ background: "#0d0d1f" }}>All Platforms</option>
          {["youtube", "instagram", "twitter", "facebook", "tiktok", "reddit", "sports_site"].map((p) => (
            <option key={p} value={p} style={{ background: "#0d0d1f" }}>{p}</option>
          ))}
        </select>
      </div>

      {/* Detections Table */}
      <div className="glass overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
          </div>
        ) : detections.length === 0 ? (
          <div className="text-center py-20">
            <Shield className="w-16 h-16 text-slate-700 mx-auto mb-4" />
            <p className="text-lg font-semibold text-slate-400">No detections found</p>
            <p className="text-slate-500 text-sm mt-2">
              Run a scan on your assets or seed demo data
            </p>
            <button onClick={handleSeedDemo} className="btn-primary inline-flex mt-4">
              <Zap className="w-4 h-4" /> Seed Demo Detections
            </button>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Asset</th>
                <th>Platform</th>
                <th>Infringing URL</th>
                <th>Similarity</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Detected</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {detections.map((d) => {
                const sev = SEVERITY_CONFIG[d.severity as keyof typeof SEVERITY_CONFIG] || SEVERITY_CONFIG.medium;
                return (
                  <motion.tr key={d.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                    <td>
                      <div className="text-sm font-medium text-slate-200 truncate max-w-[160px]">
                        {d.asset_title || `Asset #${d.asset_id}`}
                      </div>
                    </td>
                    <td>
                      <span className="flex items-center gap-1.5 text-sm">
                        {PLATFORM_ICONS[d.platform || "website"] || "🌐"}
                        <span className="text-slate-400 capitalize">{d.platform || "Unknown"}</span>
                      </span>
                    </td>
                    <td>
                      <a
                        href={d.detection_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="max-w-[200px] truncate flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300"
                      >
                        {d.domain || new URL(d.detection_url).hostname}
                        <ExternalLink className="w-3 h-3 flex-shrink-0" />
                      </a>
                    </td>
                    <td><SimilarityBar score={d.similarity_score} /></td>
                    <td><span className={`badge ${sev.className}`}>{sev.label}</span></td>
                    <td>
                      <span className={`badge ${
                        d.status === "resolved" ? "badge-success" :
                        d.status === "dmca_sent" ? "badge-warning" :
                        d.status === "false_positive" ? "badge-info" : "badge-danger"
                      }`}>
                        {d.status.replace("_", " ")}
                      </span>
                    </td>
                    <td>
                      <span className="text-xs text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(d.detected_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td>
                      <div className="flex gap-1.5">
                        {d.status === "active" && (
                          <>
                            <button
                              onClick={() => handleCreateCase(d.id)}
                              className="p-1.5 rounded-lg text-amber-400 hover:bg-amber-500/10 transition-colors"
                              title="Create DMCA case"
                            >
                              <Gavel className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleUpdateStatus(d.id, "resolved")}
                              className="p-1.5 rounded-lg text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                              title="Mark resolved"
                            >
                              <CheckCircle className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleUpdateStatus(d.id, "false_positive")}
                              className="p-1.5 rounded-lg text-slate-400 hover:bg-white/5 transition-colors"
                              title="Mark false positive"
                            >
                              <Shield className="w-4 h-4" />
                            </button>
                          </>
                        )}
                        {d.country_code && (
                          <span className="text-xs text-slate-500 flex items-center gap-0.5 ml-1">
                            <Globe className="w-3 h-3" /> {d.country_code}
                          </span>
                        )}
                      </div>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
