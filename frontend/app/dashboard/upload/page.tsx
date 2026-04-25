"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDropzone } from "react-dropzone";
import {
  Upload, X, CheckCircle, AlertCircle, Image as ImageIcon,
  Video, Shield, Tag, Loader2, Sparkles, FileText
} from "lucide-react";
import toast from "react-hot-toast";
import { assetsAPI } from "@/lib/api";
import Link from "next/link";

interface UploadedFile {
  file: File;
  preview?: string;
  status: "pending" | "uploading" | "success" | "error";
  progress: number;
  result?: any;
  error?: string;
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 ** 2)).toFixed(1)} MB`;
}

export default function UploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [metadata, setMetadata] = useState({
    tags: "",
    sport_category: "football",
    event_name: "",
    protection_level: "standard",
  });
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback((accepted: File[]) => {
    const newFiles: UploadedFile[] = accepted.map((f) => ({
      file: f,
      preview: f.type.startsWith("image/") ? URL.createObjectURL(f) : undefined,
      status: "pending",
      progress: 0,
    }));
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".jpg", ".jpeg", ".png", ".webp", ".gif"],
      "video/*": [".mp4", ".avi", ".mov", ".mkv"],
    },
    maxSize: 500 * 1024 * 1024,
  });

  const removeFile = (idx: number) => {
    setFiles((f) => f.filter((_, i) => i !== idx));
  };

  const uploadAll = async () => {
    const pending = files.filter((f) => f.status === "pending");
    if (pending.length === 0) return;
    setUploading(true);

    for (let i = 0; i < files.length; i++) {
      if (files[i].status !== "pending") continue;

      setFiles((prev) =>
        prev.map((f, idx) => idx === i ? { ...f, status: "uploading", progress: 30 } : f)
      );

      try {
        const formData = new FormData();
        formData.append("file", files[i].file);
        if (files[i].file.name.includes(".")) {
          formData.append("title", files[i].file.name.split(".")[0]);
        }
        formData.append("sport_category", metadata.sport_category);
        formData.append("event_name", metadata.event_name);
        formData.append("protection_level", metadata.protection_level);
        if (metadata.tags) {
          formData.append("tags", JSON.stringify(metadata.tags.split(",").map((t) => t.trim()).filter(Boolean)));
        }

        setFiles((prev) =>
          prev.map((f, idx) => idx === i ? { ...f, progress: 70 } : f)
        );

        const res = await assetsAPI.upload(formData);

        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === i ? { ...f, status: "success", progress: 100, result: res.data } : f
          )
        );
        toast.success(`✅ ${files[i].file.name} protected!`);
      } catch (err: any) {
        const msg = err.response?.data?.detail || "Upload failed";
        setFiles((prev) =>
          prev.map((f, idx) => idx === i ? { ...f, status: "error", error: msg } : f)
        );
        toast.error(`❌ ${files[i].file.name}: ${msg}`);
      }
    }
    setUploading(false);
  };

  const successCount = files.filter((f) => f.status === "success").length;
  const errorCount = files.filter((f) => f.status === "error").length;

  return (
    <div className="p-8 max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-black mb-2">
          <span className="gradient-text">Upload & Protect</span>
        </h1>
        <p className="text-slate-400">
          Upload your sports media assets. Our AI will fingerprint and protect them instantly.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Upload Zone */}
        <div className="col-span-2 space-y-5">
          <div
            {...getRootProps()}
            className={`upload-zone ${isDragActive ? "drag-active" : ""}`}
          >
            <input {...getInputProps()} id="file-upload-input" />
            <motion.div
              animate={{ scale: isDragActive ? 1.05 : 1 }}
              className="flex flex-col items-center gap-4"
            >
              <div className={`w-20 h-20 rounded-2xl flex items-center justify-center transition-all ${
                isDragActive
                  ? "bg-indigo-500/30 border border-indigo-500/50"
                  : "bg-indigo-500/10 border border-indigo-500/20"
              }`}>
                <Upload className={`w-10 h-10 ${isDragActive ? "text-indigo-300" : "text-indigo-400"}`} />
              </div>
              <div>
                <p className="text-lg font-semibold text-slate-200">
                  {isDragActive ? "Drop files here..." : "Drag & drop files"}
                </p>
                <p className="text-sm text-slate-400 mt-1">
                  or <span className="text-indigo-400 cursor-pointer">browse your computer</span>
                </p>
              </div>
              <div className="flex gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1"><ImageIcon className="w-3 h-3" /> JPG, PNG, WEBP, GIF</span>
                <span className="flex items-center gap-1"><Video className="w-3 h-3" /> MP4, AVI, MOV, MKV</span>
                <span>Max 500MB</span>
              </div>
            </motion.div>
          </div>

          {/* File List */}
          <AnimatePresence>
            {files.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-3"
              >
                {files.map((f, i) => (
                  <motion.div
                    key={`${f.file.name}-${i}`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className="glass-light rounded-xl p-4 flex items-center gap-4"
                  >
                    {/* Preview */}
                    <div className="w-12 h-12 rounded-lg overflow-hidden flex-shrink-0 bg-indigo-500/10 flex items-center justify-center">
                      {f.preview ? (
                        <img src={f.preview} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <Video className="w-6 h-6 text-indigo-400" />
                      )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{f.file.name}</p>
                      <p className="text-xs text-slate-500">{formatBytes(f.file.size)}</p>
                      {f.status === "uploading" && (
                        <div className="mt-2 h-1 bg-white/5 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${f.progress}%` }}
                            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                          />
                        </div>
                      )}
                      {f.status === "success" && f.result && (
                        <p className="text-xs text-emerald-400 mt-1">
                          Fingerprint: {f.result.fingerprint?.phash?.slice(0, 12)}...
                        </p>
                      )}
                      {f.status === "error" && (
                        <p className="text-xs text-red-400 mt-1">{f.error}</p>
                      )}
                    </div>

                    {/* Status Icon */}
                    <div className="flex-shrink-0">
                      {f.status === "pending" && (
                        <button onClick={() => removeFile(i)} className="text-slate-500 hover:text-red-400 transition-colors">
                          <X className="w-4 h-4" />
                        </button>
                      )}
                      {f.status === "uploading" && <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />}
                      {f.status === "success" && <CheckCircle className="w-5 h-5 text-emerald-400" />}
                      {f.status === "error" && <AlertCircle className="w-5 h-5 text-red-400" />}
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Upload Button */}
          {files.some((f) => f.status === "pending") && (
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              onClick={uploadAll}
              disabled={uploading}
              className="btn-primary w-full justify-center py-4 text-base"
            >
              {uploading ? (
                <><Loader2 className="w-5 h-5 animate-spin" /> Protecting assets...</>
              ) : (
                <><Shield className="w-5 h-5" /> Protect {files.filter((f) => f.status === "pending").length} Asset(s)</>
              )}
            </motion.button>
          )}

          {/* Results */}
          {(successCount > 0 || errorCount > 0) && !files.some((f) => f.status === "pending" || f.status === "uploading") && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="glass p-5 flex items-center justify-between"
            >
              <div>
                <p className="font-semibold">{successCount} asset(s) protected successfully</p>
                <p className="text-sm text-slate-400 mt-1">View them in your asset library</p>
              </div>
              <Link href="/dashboard/assets" className="btn-secondary py-2 px-4 text-sm">
                View Assets
              </Link>
            </motion.div>
          )}
        </div>

        {/* Metadata Panel */}
        <div className="space-y-5">
          <div className="stat-card">
            <h2 className="font-bold mb-4 flex items-center gap-2">
              <Tag className="w-4 h-4 text-indigo-400" /> Asset Metadata
            </h2>
            <div className="space-y-4">
              <div>
                <label className="form-label">Sport Category</label>
                <select
                  className="form-input"
                  value={metadata.sport_category}
                  onChange={(e) => setMetadata((m) => ({ ...m, sport_category: e.target.value }))}
                >
                  {["football", "basketball", "soccer", "tennis", "baseball", "cricket", "f1", "golf", "other"].map((s) => (
                    <option key={s} value={s} style={{ background: "#0d0d1f" }}>
                      {s.charAt(0).toUpperCase() + s.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-label">Event Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. UEFA Champions League Final"
                  value={metadata.event_name}
                  onChange={(e) => setMetadata((m) => ({ ...m, event_name: e.target.value }))}
                />
              </div>

              <div>
                <label className="form-label">Tags</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="goal, highlights, player-name"
                  value={metadata.tags}
                  onChange={(e) => setMetadata((m) => ({ ...m, tags: e.target.value }))}
                />
                <p className="text-xs text-slate-500 mt-1.5">Comma-separated</p>
              </div>

              <div>
                <label className="form-label">Protection Level</label>
                <select
                  className="form-input"
                  value={metadata.protection_level}
                  onChange={(e) => setMetadata((m) => ({ ...m, protection_level: e.target.value }))}
                >
                  <option value="standard" style={{ background: "#0d0d1f" }}>Standard</option>
                  <option value="enhanced" style={{ background: "#0d0d1f" }}>Enhanced</option>
                  <option value="maximum" style={{ background: "#0d0d1f" }}>Maximum</option>
                </select>
              </div>
            </div>
          </div>

          {/* AI Features Box */}
          <div className="stat-card space-y-3">
            <h2 className="font-bold flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" /> AI Protection
            </h2>
            {[
              "Perceptual Hash (pHash)",
              "Difference Hash (dHash)",
              "DCT Feature Vectors",
              "Invisible Watermark",
              "Gemini Content Analysis",
            ].map((feat) => (
              <div key={feat} className="flex items-center gap-2 text-sm text-slate-400">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                {feat}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
