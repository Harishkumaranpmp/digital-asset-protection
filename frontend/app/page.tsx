"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import Link from "next/link";
import { useRef, useState, useEffect } from "react";
import {
  Shield, Eye, Zap, Globe, FileText, AlertTriangle,
  ChevronRight, Play, CheckCircle, Lock, Activity,
  BarChart3, ArrowRight, Star, TrendingUp
} from "lucide-react";

const STATS = [
  { value: "99.7%", label: "Detection Accuracy", icon: Eye },
  { value: "2.3M+", label: "Assets Protected", icon: Shield },
  { value: "180+", label: "Countries Monitored", icon: Globe },
  { value: "<30s", label: "Alert Response Time", icon: Zap },
];

const FEATURES = [
  {
    icon: Shield,
    title: "AI Fingerprinting",
    description: "Multi-algorithm perceptual hashing creates unique signatures for every media asset. Even heavily modified copies are detected.",
    color: "from-indigo-500 to-purple-600",
    glow: "rgba(99, 102, 241, 0.3)",
  },
  {
    icon: Globe,
    title: "Web-Wide Scanning",
    description: "Continuous crawling across social media, streaming platforms, and millions of websites to find unauthorized copies 24/7.",
    color: "from-purple-500 to-pink-600",
    glow: "rgba(168, 85, 247, 0.3)",
  },
  {
    icon: AlertTriangle,
    title: "Real-Time Alerts",
    description: "Instant notifications the moment an infringement is detected. Know within seconds, not hours.",
    color: "from-amber-500 to-orange-600",
    glow: "rgba(245, 158, 11, 0.3)",
  },
  {
    icon: FileText,
    title: "DMCA Automation",
    description: "One-click DMCA notices with legally compliant templates. Cease & desist letters auto-populated with evidence.",
    color: "from-emerald-500 to-teal-600",
    glow: "rgba(16, 185, 129, 0.3)",
  },
  {
    icon: BarChart3,
    title: "Executive Reporting",
    description: "Board-ready analytics with geographic heat maps, trend analysis, and resolution rate tracking.",
    color: "from-cyan-500 to-blue-600",
    glow: "rgba(6, 182, 212, 0.3)",
  },
  {
    icon: Lock,
    title: "Invisible Watermarking",
    description: "LSB steganographic watermarks embedded invisibly in every protected asset for provenance proof.",
    color: "from-rose-500 to-red-600",
    glow: "rgba(244, 63, 94, 0.3)",
  },
];

const TESTIMONIALS = [
  {
    name: "Sarah Mitchell",
    role: "Head of Digital Rights, Premier Sports Network",
    text: "SportShield detected 847 unauthorized copies of our championship footage within 6 hours. We sent DMCA notices the same day.",
    rating: 5,
  },
  {
    name: "Marco Rossi",
    role: "VP Technology, Serie A Media",
    text: "The AI fingerprinting is extraordinary. It caught a modified version of our content with 30% color alteration that we'd never have found manually.",
    rating: 5,
  },
  {
    name: "Jennifer Park",
    role: "Legal Director, NBA Digital",
    text: "Reduced our copyright enforcement time by 89%. The automated DMCA generation is a game-changer for our legal team.",
    rating: 5,
  },
];

function CounterStat({ value, label, icon: Icon }: { value: string; label: string; icon: any }) {
  const [displayed, setDisplayed] = useState("0");

  useEffect(() => {
    const timer = setTimeout(() => setDisplayed(value), 500);
    return () => clearTimeout(timer);
  }, [value]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="glass text-center p-8 group hover:border-indigo-500/30 transition-all duration-500"
    >
      <div className="mb-4 flex justify-center">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-600/20 flex items-center justify-center border border-indigo-500/20 group-hover:scale-110 transition-transform">
          <Icon className="w-7 h-7 text-indigo-400" />
        </div>
      </div>
      <div className="text-4xl font-bold gradient-text mb-2">{displayed}</div>
      <div className="text-sm text-slate-400 font-medium">{label}</div>
    </motion.div>
  );
}

function FloatingOrb({ delay, className }: { delay: number; className: string }) {
  return (
    <motion.div
      className={`absolute rounded-full blur-3xl opacity-20 pointer-events-none ${className}`}
      animate={{
        scale: [1, 1.2, 1],
        opacity: [0.15, 0.25, 0.15],
      }}
      transition={{ duration: 8, repeat: Infinity, delay, ease: "easeInOut" }}
    />
  );
}

export default function LandingPage() {
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: heroRef });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, -80]);

  return (
    <div className="min-h-screen hero-gradient bg-grid overflow-x-hidden">
      {/* ─── Floating Orbs ─────────────────────────────── */}
      <FloatingOrb delay={0} className="w-96 h-96 bg-indigo-500 top-0 left-1/4" />
      <FloatingOrb delay={3} className="w-72 h-72 bg-purple-500 top-1/3 right-1/4" />
      <FloatingOrb delay={6} className="w-64 h-64 bg-cyan-500 bottom-1/3 left-1/6" />

      {/* ─── Navigation ────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-light border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold gradient-text">SportShield</span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            {["Features", "Pricing", "Docs", "Enterprise"].map((item) => (
              <a key={item} href="#" className="text-sm text-slate-400 hover:text-white transition-colors">
                {item}
              </a>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <Link href="/auth/login" className="btn-secondary py-2 px-5 text-sm">
              Sign In
            </Link>
            <Link href="/auth/register" className="btn-primary py-2 px-5 text-sm">
              Get Started <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ─── Hero Section ───────────────────────────────── */}
      <section ref={heroRef} className="relative pt-32 pb-20 px-6">
        <motion.div style={{ y: heroY }} className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-light border border-indigo-500/20 mb-8 text-sm text-indigo-300"
          >
            <div className="pulse-dot green" />
            <span>Live protection across 50+ platforms</span>
            <Activity className="w-4 h-4" />
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-6xl md:text-8xl font-black mb-6 leading-tight tracking-tight"
          >
            Protect Sports Media
            <br />
            <span className="gradient-text">From Piracy.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            AI-powered digital fingerprinting that detects unauthorized copies across the web in real time. 
            Protect your content, enforce your rights, dominate piracy.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <Link href="/auth/register" className="btn-primary text-base px-8 py-4">
              Start Protecting Now <ArrowRight className="w-5 h-5" />
            </Link>
            <Link href="/auth/login" className="btn-secondary text-base px-8 py-4">
              <Play className="w-4 h-4" /> View Demo Dashboard
            </Link>
          </motion.div>

          {/* Hero Dashboard Preview */}
          <motion.div
            initial={{ opacity: 0, y: 60, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.9, delay: 0.4 }}
            className="relative max-w-5xl mx-auto"
          >
            <div className="glass gradient-border p-1 rounded-2xl shadow-2xl shadow-indigo-500/10">
              <div className="rounded-xl overflow-hidden bg-[#080815] p-6 space-y-4">
                {/* Fake Dashboard Preview */}
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <div className="flex-1 bg-white/5 rounded-lg h-7 ml-2" />
                </div>
                <div className="grid grid-cols-4 gap-4">
                  {[
                    { label: "Assets Protected", val: "1,247", color: "text-indigo-400" },
                    { label: "Active Threats", val: "23", color: "text-red-400" },
                    { label: "DMCA Sent", val: "89", color: "text-amber-400" },
                    { label: "Resolved", val: "156", color: "text-emerald-400" },
                  ].map((s) => (
                    <div key={s.label} className="glass-light p-4 rounded-xl">
                      <div className={`text-2xl font-bold ${s.color}`}>{s.val}</div>
                      <div className="text-xs text-slate-500 mt-1">{s.label}</div>
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {["YouTube", "Instagram", "Twitter", "Reddit", "Facebook", "TikTok"].map((p, i) => (
                    <div key={p} className="glass-light rounded-lg p-3 flex items-center justify-between">
                      <span className="text-xs text-slate-400">{p}</span>
                      <span className={`text-xs font-bold ${i < 2 ? "text-red-400" : i < 4 ? "text-amber-400" : "text-slate-400"}`}>
                        {[12, 8, 5, 3, 2, 1][i]} threats
                      </span>
                    </div>
                  ))}
                </div>
                <div className="flex gap-3">
                  {[60, 80, 45, 90, 70, 85, 95].map((h, i) => (
                    <div key={i} className="flex-1 flex flex-col justify-end">
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${h}%` }}
                        transition={{ delay: 0.8 + i * 0.1, duration: 0.5 }}
                        className="rounded-t bg-gradient-to-t from-indigo-600 to-purple-500"
                        style={{ minHeight: 8 }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
            {/* Glow effect */}
            <div className="absolute inset-0 -z-10 blur-3xl opacity-30 bg-gradient-to-b from-indigo-500/20 to-transparent rounded-2xl" />
          </motion.div>
        </motion.div>
      </section>

      {/* ─── Stats ──────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {STATS.map((stat) => (
              <CounterStat key={stat.label} {...stat} />
            ))}
          </div>
        </div>
      </section>

      {/* ─── Features ───────────────────────────────────── */}
      <section className="py-20 px-6">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="max-w-7xl mx-auto"
        >
          <div className="text-center mb-16">
            <h2 className="text-5xl font-black mb-4">
              Everything You Need to
              <br />
              <span className="gradient-text">Own Your Content</span>
            </h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">
              From fingerprint to enforcement — a complete copyright protection engine built for the sports industry.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="glass p-8 group hover:scale-[1.02] transition-all duration-300"
                style={{ "--glow": feature.glow } as any}
              >
                <div
                  className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6 group-hover:shadow-lg transition-shadow`}
                  style={{ boxShadow: `0 0 0 0 ${feature.glow}` }}
                >
                  <feature.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                <p className="text-slate-400 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* ─── How It Works ────────────────────────────────── */}
      <section className="py-20 px-6">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="max-w-5xl mx-auto"
        >
          <div className="text-center mb-16">
            <h2 className="text-5xl font-black mb-4">
              <span className="gradient-text">How It Works</span>
            </h2>
            <p className="text-slate-400 text-lg">From upload to enforcement in 4 steps</p>
          </div>

          <div className="relative">
            <div className="absolute top-12 left-16 right-16 h-px bg-gradient-to-r from-transparent via-indigo-500/30 to-transparent hidden md:block" />
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              {[
                { step: "01", title: "Upload", desc: "Upload your sports media assets and add metadata", icon: "📁" },
                { step: "02", title: "Fingerprint", desc: "AI generates unique perceptual hash signatures", icon: "🔑" },
                { step: "03", title: "Scan", desc: "Crawlers scan the web and social platforms 24/7", icon: "🔍" },
                { step: "04", title: "Enforce", desc: "Auto-generate DMCA notices and track resolutions", icon: "⚡" },
              ].map((item, i) => (
                <motion.div
                  key={item.step}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.15 }}
                  className="text-center relative"
                >
                  <div className="w-24 h-24 mx-auto mb-4 glass rounded-2xl flex items-center justify-center text-4xl group-hover:scale-110 transition-transform">
                    {item.icon}
                  </div>
                  <div className="text-xs font-bold text-indigo-400 mb-2">{item.step}</div>
                  <h3 className="text-lg font-bold mb-2">{item.title}</h3>
                  <p className="text-sm text-slate-400">{item.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </section>

      {/* ─── Testimonials ───────────────────────────────── */}
      <section className="py-20 px-6">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="max-w-7xl mx-auto"
        >
          <div className="text-center mb-16">
            <h2 className="text-5xl font-black mb-4">
              Trusted by Sports
              <span className="gradient-text"> Media Leaders</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {TESTIMONIALS.map((t, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass p-8"
              >
                <div className="flex gap-1 mb-4">
                  {Array(t.rating).fill(0).map((_, j) => (
                    <Star key={j} className="w-4 h-4 text-amber-400 fill-amber-400" />
                  ))}
                </div>
                <p className="text-slate-300 leading-relaxed mb-6 italic">"{t.text}"</p>
                <div>
                  <div className="font-semibold">{t.name}</div>
                  <div className="text-sm text-slate-400">{t.role}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* ─── CTA ────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto glass gradient-border text-center p-16 relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/5 to-purple-600/5 pointer-events-none" />
          <div className="absolute -top-20 -right-20 w-64 h-64 bg-indigo-500 rounded-full blur-3xl opacity-10" />
          
          <TrendingUp className="w-16 h-16 text-indigo-400 mx-auto mb-6" />
          <h2 className="text-5xl font-black mb-4">
            Start Protecting
            <span className="gradient-text"> Today</span>
          </h2>
          <p className="text-slate-400 text-lg mb-10 max-w-xl mx-auto">
            Join hundreds of sports organizations protecting their digital assets with SportShield's AI platform.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/auth/register" className="btn-primary text-base px-10 py-4">
              Create Free Account <ArrowRight className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              No credit card required
            </div>
          </div>
        </motion.div>
      </section>

      {/* ─── Footer ─────────────────────────────────────── */}
      <footer className="py-12 px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold gradient-text">SportShield</span>
          </div>
          <p className="text-slate-500 text-sm">
            © 2024 SportShield AI. All rights reserved. Built for the future of sports media protection.
          </p>
          <div className="flex gap-6 text-sm text-slate-500">
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href="#" className="hover:text-white transition-colors">API Docs</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
