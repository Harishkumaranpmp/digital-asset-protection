"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  LayoutDashboard, Upload, Shield, AlertTriangle, Gavel,
  BarChart3, Bell, Settings, LogOut, ChevronRight, Activity
} from "lucide-react";
import { useAuth, AuthProvider } from "@/lib/auth-context";
import { Toaster } from "react-hot-toast";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/upload", label: "Upload Assets", icon: Upload },
  { href: "/dashboard/assets", label: "Asset Library", icon: Shield },
  { href: "/dashboard/detections", label: "Detections", icon: AlertTriangle },
  { href: "/dashboard/enforcement", label: "Enforcement", icon: Gavel },
  { href: "/dashboard/reports", label: "Reports", icon: BarChart3 },
  { href: "/dashboard/alerts", label: "Alerts", icon: Bell },
];

function DashboardSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="sidebar flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-white/5">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:scale-110 transition-transform">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-sm gradient-text">SportShield</div>
            <div className="text-xs text-slate-500">Protection Platform</div>
          </div>
        </Link>
      </div>

      {/* Live indicator */}
      <div className="px-4 py-3 mx-4 mt-4 glass-light rounded-xl flex items-center gap-2">
        <div className="pulse-dot green" />
        <span className="text-xs text-emerald-400 font-medium">Protection Active</span>
        <Activity className="w-3 h-3 text-emerald-400 ml-auto" />
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <div className="px-4 mb-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Navigation</span>
        </div>
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link key={href} href={href} className={`sidebar-link ${active ? "active" : ""}`}>
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span className="flex-1">{label}</span>
              {active && <ChevronRight className="w-3 h-3 opacity-50" />}
            </Link>
          );
        })}
      </nav>

      {/* User info */}
      <div className="p-4 border-t border-white/5">
        <div className="glass-light rounded-xl p-3 mb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-sm font-bold">
              {user?.full_name?.[0] || user?.username?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{user?.full_name || user?.username}</div>
              <div className="text-xs text-slate-500 truncate">{user?.org_name || user?.role}</div>
            </div>
          </div>
        </div>
        <button
          onClick={logout}
          className="sidebar-link w-full text-red-400 hover:text-red-300 hover:bg-red-500/10"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen hero-gradient flex items-center justify-center">
        <div className="glass p-8 flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center animate-pulse">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <p className="text-slate-400 text-sm">Loading SportShield...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return null;
  return <>{children}</>;
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <AuthGuard>
        <div className="flex min-h-screen bg-[#080815]">
          <DashboardSidebar />
          <main className="flex-1 ml-[260px] min-h-screen overflow-auto">
            {children}
          </main>
        </div>
      </AuthGuard>
    </AuthProvider>
  );
}
