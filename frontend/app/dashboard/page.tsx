"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Shield, AlertTriangle, Eye, Gavel, TrendingUp, Activity,
  Globe, Zap, RefreshCw, ChevronRight, Clock, Sparkles
} from "lucide-react";
import Link from "next/link";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar
} from "recharts";
import { assetsAPI, detectionsAPI, enforcementAPI, reportsAPI } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import toast from "react-hot-toast";

const SEVERITY_COLORS = {
  critical: "#dc2626",
  high: "#f59e0b",
  medium: "#6366f1",
  low: "#10b981",
};

const PIE_COLORS = ["#ef4444", "#f59e0b", "#6366f1", "#10b981"];

function StatCard({
  title, value, subtitle, icon: Icon, color, href, delta,
}: {
  title: string; value: string | number; subtitle?: string;
  icon: any; color: string; href?: string; delta?: string;
}) {
  const content = (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="stat-card group cursor-pointer"
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {delta && (
          <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {delta}
          </span>
        )}
      </div>
      <div className="text-3xl font-black mb-1">{value}</div>
      <div className="text-sm font-medium text-slate-300">{title}</div>
      {subtitle && <div className="text-xs text-slate-500 mt-1">{subtitle}</div>}
      {href && (
        <div className="mt-4 flex items-center gap-1 text-xs text-indigo-400 group-hover:text-indigo-300 transition-colors">
          View details <ChevronRight className="w-3 h-3" />
        </div>
      )}
    </motion.div>
  );

  return href ? <Link href={href}>{content}</Link> : content;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [assetStats, setAssetStats] = useState<any>(null);
  const [detectionStats, setDetectionStats] = useState<any>(null);
  const [enforcementStats, setEnforcementStats] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const [assets, detections, enforcement, sum] = await Promise.allSettled([
        assetsAPI.stats(),
        detectionsAPI.stats(),
        enforcementAPI.stats(),
        reportsAPI.summary(),
      ]);

      if (assets.status === "fulfilled") setAssetStats(assets.value.data);
      if (detections.status === "fulfilled") setDetectionStats(detections.value.data);
      if (enforcement.status === "fulfilled") setEnforcementStats(enforcement.value.data);
      if (sum.status === "fulfilled") setSummary(sum.value.data);
    } catch (err) {
      console.error("Dashboard load error:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const handleSeedDemo = async () => {
    try {
      setRefreshing(true);
      await detectionsAPI.seedDemo();
      await loadData();
      toast.success("Demo data seeded successfully!");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Make sure you have uploaded at least one asset first.");
    } finally {
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    toast.success("Dashboard refreshed");
  };

  const trendData = detectionStats?.trend_7days || [];
  const platformData = Object.entries(detectionStats?.platform_breakdown || {}).map(
    ([name, value]) => ({ name, value })
  );
  const statusData = assetStats
    ? [
        { name: "Protected", value: assetStats.protected, color: "#10b981" },
        { name: "At Risk", value: assetStats.at_risk, color: "#f59e0b" },
        { name: "Violated", value: assetStats.violated, color: "#ef4444" },
      ]
    : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="glass p-8 flex flex-col items-center gap-4">
          <Shield className="w-10 h-10 text-indigo-400 animate-pulse" />
          <p className="text-slate-400 text-sm">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black">
            Welcome back, <span className="gradient-text">{user?.full_name?.split(" ")[0] || user?.username}</span>
          </h1>
          <p className="text-slate-400 mt-1 flex items-center gap-2">
            <div className="pulse-dot green" />
            Protection system active — monitoring in real time
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleSeedDemo}
            disabled={refreshing}
            className="btn-secondary py-2 px-4 text-sm border-purple-500/30 text-purple-400 hover:bg-purple-500/10"
          >
            <Sparkles className="w-4 h-4" /> Seed Demo
          </button>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-secondary py-2 px-4 text-sm"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link href="/dashboard/upload" className="btn-primary py-2 px-4 text-sm">
            <Shield className="w-4 h-4" /> Protect Asset
          </Link>
        </div>
      </div>

      {/* Threat Score Banner */}
      {summary && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass gradient-border p-6 flex items-center justify-between"
        >
          <div className="flex items-center gap-6">
            <div className="relative w-20 h-20">
              <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                <circle cx="40" cy="40" r="32" fill="none" stroke="rgba(99,102,241,0.1)" strokeWidth="6" />
                <circle
                  cx="40" cy="40" r="32" fill="none"
                  stroke={summary.threat_score > 60 ? "#ef4444" : summary.threat_score > 30 ? "#f59e0b" : "#10b981"}
                  strokeWidth="6" strokeLinecap="round"
                  strokeDasharray={`${(summary.threat_score / 100) * 201} 201`}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xl font-black">{summary.threat_score}</span>
              </div>
            </div>
            <div>
              <div className="text-lg font-bold">
                Threat Score — <span className={summary.threat_score > 60 ? "text-red-400" : summary.threat_score > 30 ? "text-amber-400" : "text-emerald-400"}>
                  {summary.threat_score > 60 ? "High Risk" : summary.threat_score > 30 ? "Medium Risk" : "Low Risk"}
                </span>
              </div>
              <p className="text-slate-400 text-sm mt-1">
                {summary.detections.critical} critical threats · {summary.detections.active} active detections
              </p>
            </div>
          </div>
          <Link href="/dashboard/detections" className="btn-danger">
            View Threats <ChevronRight className="w-4 h-4" />
          </Link>
        </motion.div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Assets" value={assetStats?.total_assets ?? "—"}
          icon={Shield} color="bg-gradient-to-br from-indigo-500 to-purple-600"
          href="/dashboard/assets" delta="+12%"
          subtitle={`${assetStats?.images ?? 0} images · ${assetStats?.videos ?? 0} videos`}
        />
        <StatCard
          title="Active Threats" value={detectionStats?.active ?? "—"}
          icon={AlertTriangle} color="bg-gradient-to-br from-red-500 to-orange-600"
          href="/dashboard/detections"
          subtitle={`${detectionStats?.critical ?? 0} critical`}
        />
        <StatCard
          title="Total Detections" value={detectionStats?.total ?? "—"}
          icon={Eye} color="bg-gradient-to-br from-amber-500 to-orange-500"
          href="/dashboard/detections" delta="↑ 24%"
        />
        <StatCard
          title="Cases Filed" value={enforcementStats?.total_cases ?? "—"}
          icon={Gavel} color="bg-gradient-to-br from-emerald-500 to-teal-600"
          href="/dashboard/enforcement"
          subtitle={`${enforcementStats?.resolved ?? 0} resolved`}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-6">
        {/* Detection Trend - spans 2 cols */}
        <div className="col-span-2 stat-card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-bold">Detection Trend</h2>
              <p className="text-sm text-slate-400">Last 7 days</p>
            </div>
            <Activity className="w-5 h-5 text-indigo-400" />
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="threatGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false}
                tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ background: "#0d0d1f", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 8, color: "#e2e8f0" }}
              />
              <Area type="monotone" dataKey="count" stroke="#6366f1" fill="url(#threatGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Asset Status Pie */}
        <div className="stat-card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-bold">Asset Status</h2>
              <p className="text-sm text-slate-400">Protection overview</p>
            </div>
            <Shield className="w-5 h-5 text-indigo-400" />
          </div>
          {statusData.some((d) => d.value > 0) ? (
            <>
              <ResponsiveContainer width="100%" height={140}>
                <PieChart>
                  <Pie data={statusData} cx="50%" cy="50%" innerRadius={40} outerRadius={65}
                    paddingAngle={3} dataKey="value">
                    {statusData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#0d0d1f", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-2">
                {statusData.map((d) => (
                  <div key={d.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                      <span className="text-slate-400">{d.name}</span>
                    </div>
                    <span className="font-semibold">{d.value}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-40 text-slate-500">
              <Shield className="w-10 h-10 mb-2 opacity-30" />
              <p className="text-sm">Upload assets to get started</p>
            </div>
          )}
        </div>
      </div>

      {/* Platform Breakdown + Quick Actions */}
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 stat-card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-bold">Platform Breakdown</h2>
              <p className="text-sm text-slate-400">Detections by platform</p>
            </div>
            <Globe className="w-5 h-5 text-indigo-400" />
          </div>
          {platformData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={platformData} layout="vertical" barCategoryGap={6}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.04)" />
                <XAxis type="number" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis dataKey="name" type="category" tick={{ fill: "#94a3b8", fontSize: 11 }} tickLine={false} axisLine={false} width={80} />
                <Tooltip contentStyle={{ background: "#0d0d1f", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 8, color: "#e2e8f0" }} />
                <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center h-40 text-slate-500">
              <Globe className="w-10 h-10 mb-2 opacity-30" />
              <p className="text-sm">No detections yet — trigger a scan</p>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="stat-card space-y-3">
          <h2 className="text-lg font-bold mb-2">Quick Actions</h2>
          {[
            { label: "Protect New Asset", href: "/dashboard/upload", icon: Shield, color: "text-indigo-400" },
            { label: "View All Threats", href: "/dashboard/detections", icon: AlertTriangle, color: "text-red-400" },
            { label: "Generate Report", href: "/dashboard/reports", icon: TrendingUp, color: "text-amber-400" },
            { label: "Manage Cases", href: "/dashboard/enforcement", icon: Gavel, color: "text-emerald-400" },
          ].map(({ label, href, icon: Icon, color }) => (
            <Link key={href} href={href}
              className="flex items-center gap-3 p-3 glass-light rounded-xl hover:border-indigo-500/30 transition-all group">
              <Icon className={`w-5 h-5 ${color}`} />
              <span className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">
                {label}
              </span>
              <ChevronRight className="w-4 h-4 text-slate-600 ml-auto group-hover:text-indigo-400 transition-colors" />
            </Link>
          ))}

          <div className="pt-2 border-t border-white/5">
            <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span>Protection Rate</span>
              <span className="text-emerald-400 font-semibold">{assetStats?.protection_rate ?? 0}%</span>
            </div>
            <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${assetStats?.protection_rate ?? 0}%` }}
                transition={{ duration: 1, delay: 0.5 }}
                className="h-full bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-full"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
