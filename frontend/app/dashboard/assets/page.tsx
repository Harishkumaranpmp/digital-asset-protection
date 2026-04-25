"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield, Search, Filter, Trash2, Eye, Scan, Image as Img,
  Video, Clock, CheckCircle, AlertTriangle, XCircle, Loader2, ChevronRight
} from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";
import { assetsAPI, detectionsAPI, Asset } from "@/lib/api";

const STATUS_CONFIG: Record<string, { label: string; className: string; icon: any }> = {
  processing: { label: "Processing", className: "badge-info", icon: Loader2 },
  protected: { label: "Protected", className: "badge-success", icon: CheckCircle },
  at_risk: { label: "At Risk", className: "badge-warning", icon: AlertTriangle },
  violated: { label: "Violated", className: "badge-critical", icon: XCircle },
};

function formatBytes(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 ** 2).toFixed(1)} MB`;
}

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterType, setFilterType] = useState("");
  const [scanningId, setScanningId] = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await assetsAPI.list({
        search: search || undefined,
        status: filterStatus || undefined,
        file_type: filterType || undefined,
        limit: 50,
      });
      setAssets(res.data.assets);
      setTotal(res.data.total);
    } catch {
      toast.error("Failed to load assets");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [search, filterStatus, filterType]);

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Delete "${name}"?`)) return;
    try {
      await assetsAPI.delete(id);
      setAssets((a) => a.filter((x) => x.id !== id));
      toast.success("Asset deleted");
    } catch {
      toast.error("Delete failed");
    }
  };

  const handleScan = async (id: number) => {
    setScanningId(id);
    try {
      const res = await detectionsAPI.scan(id);
      const count = res.data.new_detections;
      if (count > 0) {
        toast.success(`🚨 ${count} new infringement(s) detected!`);
      } else {
        toast.success("✅ No new infringements found");
      }
      load(); // Refresh
    } catch {
      toast.error("Scan failed — is the backend running?");
    } finally {
      setScanningId(null);
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-black mb-1">
            <span className="gradient-text">Asset Library</span>
          </h1>
          <p className="text-slate-400">{total} protected assets in your library</p>
        </div>
        <Link href="/dashboard/upload" className="btn-primary py-2 px-5">
          <Shield className="w-4 h-4" /> Add Assets
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search assets..."
            className="form-input pl-10 py-2.5"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select className="form-input py-2.5 w-auto" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="" style={{ background: "#0d0d1f" }}>All Statuses</option>
          <option value="protected" style={{ background: "#0d0d1f" }}>Protected</option>
          <option value="at_risk" style={{ background: "#0d0d1f" }}>At Risk</option>
          <option value="violated" style={{ background: "#0d0d1f" }}>Violated</option>
        </select>
        <select className="form-input py-2.5 w-auto" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          <option value="" style={{ background: "#0d0d1f" }}>All Types</option>
          <option value="image" style={{ background: "#0d0d1f" }}>Images</option>
          <option value="video" style={{ background: "#0d0d1f" }}>Videos</option>
        </select>
      </div>

      {/* Table */}
      <div className="glass overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
          </div>
        ) : assets.length === 0 ? (
          <div className="text-center py-20">
            <Shield className="w-16 h-16 text-slate-700 mx-auto mb-4" />
            <p className="text-lg font-semibold text-slate-400">No assets found</p>
            <p className="text-slate-500 text-sm mt-2">Upload your first sports media asset to get started</p>
            <Link href="/dashboard/upload" className="btn-primary inline-flex mt-4">Upload Asset</Link>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Asset</th>
                <th>Type</th>
                <th>Sport</th>
                <th>Fingerprint</th>
                <th>Status</th>
                <th>Threats</th>
                <th>Uploaded</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {assets.map((asset) => {
                  const st = STATUS_CONFIG[asset.status] || STATUS_CONFIG.processing;
                  return (
                    <motion.tr
                      key={asset.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                    >
                      <td>
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                            {asset.file_type === "video" ? (
                              <Video className="w-5 h-5 text-indigo-400" />
                            ) : (
                              <Img className="w-5 h-5 text-indigo-400" />
                            )}
                          </div>
                          <div>
                            <div className="font-medium text-slate-200 text-sm truncate max-w-[200px]">
                              {asset.title || asset.original_filename}
                            </div>
                            <div className="text-xs text-slate-500">{formatBytes(asset.file_size)}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="text-xs font-medium text-slate-400 uppercase">{asset.file_type}</span>
                      </td>
                      <td>
                        <span className="text-xs text-slate-400">{asset.sport_category || "—"}</span>
                      </td>
                      <td>
                        {asset.watermark_id ? (
                          <code className="text-xs text-indigo-300 font-mono bg-indigo-500/10 px-2 py-0.5 rounded">
                            {asset.watermark_id.slice(0, 10)}...
                          </code>
                        ) : <span className="text-slate-600">—</span>}
                      </td>
                      <td>
                        <span className={`badge ${st.className}`}>
                          <st.icon className="w-3 h-3" />
                          {st.label}
                        </span>
                      </td>
                      <td>
                        <span className={`text-sm font-semibold ${asset.detections_count > 0 ? "text-red-400" : "text-slate-500"}`}>
                          {asset.detections_count}
                        </span>
                      </td>
                      <td>
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(asset.created_at).toLocaleDateString()}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleScan(asset.id)}
                            disabled={scanningId === asset.id}
                            className="p-1.5 rounded-lg text-indigo-400 hover:bg-indigo-500/10 transition-colors"
                            title="Run scan"
                          >
                            {scanningId === asset.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Scan className="w-4 h-4" />
                            )}
                          </button>
                          <Link
                            href={`/dashboard/detections?asset_id=${asset.id}`}
                            className="p-1.5 rounded-lg text-slate-400 hover:bg-white/5 transition-colors"
                            title="View detections"
                          >
                            <Eye className="w-4 h-4" />
                          </Link>
                          <button
                            onClick={() => handleDelete(asset.id, asset.title || asset.original_filename)}
                            className="p-1.5 rounded-lg text-slate-500 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  );
                })}
              </AnimatePresence>
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
