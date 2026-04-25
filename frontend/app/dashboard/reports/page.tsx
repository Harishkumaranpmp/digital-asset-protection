"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart3, Download, TrendingUp, Shield, AlertTriangle,
  Gavel, FileText, Loader2
} from "lucide-react";
import toast from "react-hot-toast";
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip
} from "recharts";
import { reportsAPI } from "@/lib/api";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ReportsPage() {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    reportsAPI.summary()
      .then((r) => setSummary(r.data))
      .catch(() => toast.error("Failed to load report"))
      .finally(() => setLoading(false));
  }, []);

  const handleDownload = async (type: "detections" | "assets") => {
    setDownloading(type);
    try {
      const res = type === "detections"
        ? await reportsAPI.downloadDetectionsCSV()
        : await reportsAPI.downloadAssetsCSV();
      downloadBlob(res.data, `sportshield_${type}_${new Date().toISOString().slice(0, 10)}.csv`);
      toast.success(`${type} report downloaded!`);
    } catch {
      toast.error("Download failed");
    } finally {
      setDownloading(null);
    }
  };

  const radarData = summary ? [
    { subject: "Assets", A: summary.assets.protection_rate, fullMark: 100 },
    { subject: "Detections", A: Math.max(0, 100 - (summary.detections.active * 5)), fullMark: 100 },
    { subject: "Enforcement", A: summary.enforcement.resolution_rate, fullMark: 100 },
    { subject: "Response", A: 85, fullMark: 100 },
    { subject: "Coverage", A: 72, fullMark: 100 },
  ] : [];

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-black mb-1">
            <span className="gradient-text">Reports & Analytics</span>
          </h1>
          <p className="text-slate-400">Generate and download executive reports</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => handleDownload("assets")}
            disabled={!!downloading}
            className="btn-secondary py-2 px-4 text-sm"
          >
            {downloading === "assets" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Assets CSV
          </button>
          <button
            onClick={() => handleDownload("detections")}
            disabled={!!downloading}
            className="btn-primary py-2 px-4 text-sm"
          >
            {downloading === "detections" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Detections CSV
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
        </div>
      ) : summary ? (
        <div className="space-y-8">
          {/* Executive Summary Cards */}
          <div className="grid grid-cols-3 gap-6">
            {/* Assets */}
            <div className="stat-card">
              <div className="flex items-center gap-3 mb-4">
                <Shield className="w-6 h-6 text-indigo-400" />
                <h2 className="font-bold">Asset Overview</h2>
              </div>
              <div className="space-y-3">
                {[
                  { label: "Total Assets", value: summary.assets.total, color: "text-white" },
                  { label: "Protected", value: summary.assets.protected, color: "text-emerald-400" },
                  { label: "At Risk", value: summary.assets.at_risk, color: "text-amber-400" },
                  { label: "Violated", value: summary.assets.violated, color: "text-red-400" },
                ].map(({ label, value, color }) => (
                  <div key={label} className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">{label}</span>
                    <span className={`font-bold ${color}`}>{value}</span>
                  </div>
                ))}
                <div className="pt-2 border-t border-white/5">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">Protection Rate</span>
                    <span className="text-emerald-400 font-bold">{summary.assets.protection_rate}%</span>
                  </div>
                  <div className="mt-2 h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${summary.assets.protection_rate}%` }}
                      transition={{ duration: 1 }}
                      className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Detections */}
            <div className="stat-card">
              <div className="flex items-center gap-3 mb-4">
                <AlertTriangle className="w-6 h-6 text-amber-400" />
                <h2 className="font-bold">Detection Summary</h2>
              </div>
              <div className="space-y-3">
                {[
                  { label: "Total Found", value: summary.detections.total, color: "text-white" },
                  { label: "Active", value: summary.detections.active, color: "text-red-400" },
                  { label: "Resolved", value: summary.detections.resolved, color: "text-emerald-400" },
                  { label: "Critical", value: summary.detections.critical, color: "text-red-500" },
                ].map(({ label, value, color }) => (
                  <div key={label} className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">{label}</span>
                    <span className={`font-bold ${color}`}>{value}</span>
                  </div>
                ))}
                <div className="pt-2 border-t border-white/5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">Generated:</span>
                    <span className="text-xs text-slate-400">
                      {new Date(summary.generated_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Enforcement */}
            <div className="stat-card">
              <div className="flex items-center gap-3 mb-4">
                <Gavel className="w-6 h-6 text-purple-400" />
                <h2 className="font-bold">Enforcement</h2>
              </div>
              <div className="space-y-3">
                {[
                  { label: "Total Cases", value: summary.enforcement.total_cases, color: "text-white" },
                  { label: "Resolved", value: summary.enforcement.resolved, color: "text-emerald-400" },
                ].map(({ label, value, color }) => (
                  <div key={label} className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">{label}</span>
                    <span className={`font-bold ${color}`}>{value}</span>
                  </div>
                ))}
                <div className="pt-2 border-t border-white/5">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">Resolution Rate</span>
                    <span className="text-purple-400 font-bold">{summary.enforcement.resolution_rate}%</span>
                  </div>
                  <div className="mt-2 h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${summary.enforcement.resolution_rate}%` }}
                      transition={{ duration: 1, delay: 0.3 }}
                      className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full"
                    />
                  </div>
                </div>

                {/* Threat Score */}
                <div className="pt-2 border-t border-white/5 text-center">
                  <div className="text-2xl font-black" style={{
                    color: summary.threat_score > 60 ? "#ef4444" : summary.threat_score > 30 ? "#f59e0b" : "#10b981"
                  }}>
                    {summary.threat_score}
                  </div>
                  <div className="text-xs text-slate-500">Threat Score</div>
                </div>
              </div>
            </div>
          </div>

          {/* Radar Chart */}
          <div className="stat-card">
            <h2 className="font-bold mb-2 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-400" />
              Protection Health Radar
            </h2>
            <p className="text-sm text-slate-400 mb-6">Multidimensional view of your security posture</p>
            <ResponsiveContainer width="100%" height={320}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(99,102,241,0.1)" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <Radar name="Score" dataKey="A" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Export Section */}
          <div className="glass p-6">
            <h2 className="font-bold mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-400" />
              Export Reports
            </h2>
            <div className="grid grid-cols-2 gap-4">
              {[
                { title: "Assets Report", desc: "All protected assets with fingerprint details", type: "assets" as const },
                { title: "Detections Report", desc: "All detected infringements with similarity scores", type: "detections" as const },
              ].map(({ title, desc, type }) => (
                <div key={type} className="glass-light p-5 rounded-xl flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-200">{title}</p>
                    <p className="text-xs text-slate-500 mt-1">{desc}</p>
                  </div>
                  <button
                    onClick={() => handleDownload(type)}
                    disabled={!!downloading}
                    className="btn-primary py-2 px-3 text-sm ml-4"
                  >
                    {downloading === type ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Download className="w-4 h-4" />
                    )}
                    CSV
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-20 text-slate-400">No data available. Upload assets to generate reports.</div>
      )}
    </div>
  );
}
