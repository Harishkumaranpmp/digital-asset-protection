"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, Check, CheckCheck, Shield, AlertTriangle, Gavel, Info, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { alertsAPI } from "@/lib/api";

const SEVERITY_CONFIG = {
  info: { icon: Info, color: "text-indigo-400", bg: "bg-indigo-500/10" },
  warning: { icon: AlertTriangle, color: "text-amber-400", bg: "bg-amber-500/10" },
  danger: { icon: AlertTriangle, color: "text-red-400", bg: "bg-red-500/10" },
  critical: { icon: AlertTriangle, color: "text-red-400", bg: "bg-red-500/20" },
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await alertsAPI.list({ limit: 100 });
      setAlerts(res.data.alerts);
      setUnread(res.data.unread);
    } catch {
      toast.error("Failed to load alerts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleMarkRead = async (id: number) => {
    try {
      await alertsAPI.markRead(id);
      setAlerts((a) => a.map((x) => x.id === id ? { ...x, is_read: true } : x));
      setUnread((n) => Math.max(0, n - 1));
    } catch { }
  };

  const handleMarkAllRead = async () => {
    try {
      await alertsAPI.markAllRead();
      setAlerts((a) => a.map((x) => ({ ...x, is_read: true })));
      setUnread(0);
      toast.success("All alerts marked as read");
    } catch {
      toast.error("Failed");
    }
  };

  return (
    <div className="p-8 max-w-3xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-black mb-1 flex items-center gap-3">
            <span className="gradient-text">Alert Center</span>
            {unread > 0 && (
              <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-red-500 text-white text-xs font-bold">
                {unread}
              </span>
            )}
          </h1>
          <p className="text-slate-400">{alerts.length} alerts · {unread} unread</p>
        </div>
        {unread > 0 && (
          <button onClick={handleMarkAllRead} className="btn-secondary py-2 px-4 text-sm">
            <CheckCheck className="w-4 h-4" /> Mark All Read
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
        </div>
      ) : alerts.length === 0 ? (
        <div className="glass text-center py-20">
          <Bell className="w-16 h-16 text-slate-700 mx-auto mb-4" />
          <p className="text-lg font-semibold text-slate-400">No alerts yet</p>
          <p className="text-slate-500 text-sm mt-2">Alerts will appear here when infringements are detected</p>
        </div>
      ) : (
        <div className="space-y-3">
          <AnimatePresence>
            {alerts.map((alert) => {
              const conf = SEVERITY_CONFIG[alert.severity as keyof typeof SEVERITY_CONFIG] || SEVERITY_CONFIG.info;
              const Icon = conf.icon;
              return (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className={`glass-light rounded-xl p-4 flex items-start gap-4 transition-all ${
                    !alert.is_read ? "border border-indigo-500/20" : "opacity-60"
                  }`}
                >
                  <div className={`w-10 h-10 rounded-xl ${conf.bg} flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-5 h-5 ${conf.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-sm text-slate-200">{alert.title}</p>
                      {!alert.is_read && (
                        <div className="w-2 h-2 rounded-full bg-indigo-400 flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-sm text-slate-400 mt-0.5">{alert.message}</p>
                    <p className="text-xs text-slate-600 mt-1">
                      {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                  {!alert.is_read && (
                    <button
                      onClick={() => handleMarkRead(alert.id)}
                      className="flex-shrink-0 p-1.5 rounded-lg text-slate-500 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                      title="Mark as read"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                  )}
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
