import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  spring,
  Sequence,
} from "remotion";

// ── Brand tokens ──────────────────────────────────────────────────
const BRAND = {
  bg: "#0a0e1a",
  primary: "#6366f1",   // indigo
  accent: "#22d3ee",    // cyan
  white: "#f8fafc",
  muted: "#94a3b8",
  gradient: "linear-gradient(135deg, #6366f1 0%, #22d3ee 100%)",
};

// ── Helpers ───────────────────────────────────────────────────────
function easeOut(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

function fadeIn(frame: number, start: number, duration: number): number {
  return easeOut(clamp((frame - start) / duration, 0, 1));
}

function fadeOut(frame: number, start: number, duration: number): number {
  return 1 - easeOut(clamp((frame - start) / duration, 0, 1));
}

// ── Scene 1: Logo reveal (frames 0 – 179, 6 s) ───────────────────
const SceneLogo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Logo circle scale spring
  const circleScale = spring({ frame, fps, config: { damping: 18, stiffness: 120 }, durationInFrames: 50 });

  // "dk" text inside circle
  const letterOpacity = fadeIn(frame, 20, 25);

  // "apps" wordmark beside circle
  const wordmarkX = interpolate(frame, [35, 70], [60, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const wordmarkOpacity = fadeIn(frame, 35, 30);

  // Tagline below
  const taglineOpacity = fadeIn(frame, 70, 30);

  // Scene exit fade
  const exitOpacity = frame < 150 ? 1 : fadeOut(frame, 150, 30);

  return (
    <AbsoluteFill style={{ background: BRAND.bg, justifyContent: "center", alignItems: "center", opacity: exitOpacity }}>
      {/* Ambient glow */}
      <div style={{
        position: "absolute",
        width: 600,
        height: 600,
        borderRadius: "50%",
        background: `radial-gradient(circle, ${BRAND.primary}22 0%, transparent 70%)`,
        transform: `scale(${circleScale})`,
      }} />

      {/* Logo lockup */}
      <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
        {/* Circle mark */}
        <div style={{
          width: 120,
          height: 120,
          borderRadius: "50%",
          background: BRAND.gradient,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transform: `scale(${circleScale})`,
          boxShadow: `0 0 60px ${BRAND.primary}66`,
        }}>
          <span style={{
            fontSize: 48,
            fontWeight: 800,
            color: BRAND.white,
            fontFamily: "system-ui, -apple-system, sans-serif",
            letterSpacing: -2,
            opacity: letterOpacity,
          }}>
            dk
          </span>
        </div>

        {/* Wordmark */}
        <div style={{
          transform: `translateX(${wordmarkX}px)`,
          opacity: wordmarkOpacity,
        }}>
          <span style={{
            fontSize: 72,
            fontWeight: 800,
            color: BRAND.white,
            fontFamily: "system-ui, -apple-system, sans-serif",
            letterSpacing: -3,
          }}>
            apps
          </span>
        </div>
      </div>

      {/* Tagline */}
      <div style={{
        position: "absolute",
        bottom: "38%",
        opacity: taglineOpacity,
        transform: `translateY(${interpolate(taglineOpacity, [0, 1], [20, 0])}px)`,
      }}>
        <span style={{
          fontSize: 22,
          color: BRAND.accent,
          fontFamily: "system-ui, -apple-system, sans-serif",
          letterSpacing: 6,
          textTransform: "uppercase",
          fontWeight: 500,
        }}>
          Build. Ship. Scale.
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 2: Feature highlights (frames 180 – 389, ~6.7 s) ───────
interface FeatureProps {
  icon: string;
  title: string;
  desc: string;
  delay: number;
}

const FeatureCard: React.FC<FeatureProps & { frame: number }> = ({ icon, title, desc, delay, frame }) => {
  const opacity = fadeIn(frame, delay, 25);
  const y = interpolate(frame, [delay, delay + 25], [40, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <div style={{
      opacity,
      transform: `translateY(${y}px)`,
      background: "#ffffff08",
      border: `1px solid ${BRAND.primary}44`,
      borderRadius: 20,
      padding: "32px 40px",
      width: 320,
      backdropFilter: "blur(10px)",
    }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>{icon}</div>
      <div style={{ fontSize: 24, fontWeight: 700, color: BRAND.white, marginBottom: 8, fontFamily: "system-ui, sans-serif" }}>{title}</div>
      <div style={{ fontSize: 16, color: BRAND.muted, fontFamily: "system-ui, sans-serif", lineHeight: 1.6 }}>{desc}</div>
    </div>
  );
};

const SceneFeatures: React.FC = () => {
  const frame = useCurrentFrame();

  const titleOpacity = fadeIn(frame, 10, 25);
  const exitOpacity = frame < 170 ? 1 : fadeOut(frame, 170, 30);

  const features: FeatureProps[] = [
    { icon: "⚡", title: "Fast by default", desc: "Optimized builds and instant deploys for modern teams.", delay: 30 },
    { icon: "🔒", title: "Secure & reliable", desc: "Enterprise-grade security baked into every layer.", delay: 55 },
    { icon: "🚀", title: "Scale effortlessly", desc: "From prototype to production without re-architecture.", delay: 80 },
  ];

  return (
    <AbsoluteFill style={{ background: BRAND.bg, justifyContent: "center", alignItems: "center", flexDirection: "column", gap: 60, opacity: exitOpacity }}>
      {/* Section heading */}
      <div style={{ opacity: titleOpacity, transform: `translateY(${interpolate(titleOpacity, [0, 1], [-20, 0])}px)` }}>
        <span style={{
          fontSize: 44,
          fontWeight: 700,
          color: BRAND.white,
          fontFamily: "system-ui, sans-serif",
          letterSpacing: -1,
        }}>
          Everything your team needs
        </span>
      </div>

      {/* Cards row */}
      <div style={{ display: "flex", gap: 32 }}>
        {features.map((f) => (
          <FeatureCard key={f.title} {...f} frame={frame} />
        ))}
      </div>

      {/* Decorative line */}
      <div style={{
        width: interpolate(frame, [15, 60], [0, 800], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        height: 2,
        background: BRAND.gradient,
        borderRadius: 2,
        position: "absolute",
        bottom: "22%",
      }} />
    </AbsoluteFill>
  );
};

// ── Scene 3: Stats / social proof (frames 390 – 509, 4 s) ────────
interface StatProps {
  value: string;
  label: string;
  delay: number;
}

const StatBlock: React.FC<StatProps & { frame: number }> = ({ value, label, delay, frame }) => {
  const opacity = fadeIn(frame, delay, 20);
  const scale = interpolate(frame, [delay, delay + 20], [0.8, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <div style={{ opacity, transform: `scale(${scale})`, textAlign: "center", minWidth: 200 }}>
      <div style={{
        fontSize: 64,
        fontWeight: 800,
        background: BRAND.gradient,
        WebkitBackgroundClip: "text",
        WebkitTextFillColor: "transparent",
        fontFamily: "system-ui, sans-serif",
        letterSpacing: -2,
        lineHeight: 1,
      }}>
        {value}
      </div>
      <div style={{ fontSize: 18, color: BRAND.muted, fontFamily: "system-ui, sans-serif", marginTop: 8, letterSpacing: 1 }}>
        {label}
      </div>
    </div>
  );
};

const SceneStats: React.FC = () => {
  const frame = useCurrentFrame();
  const exitOpacity = frame < 90 ? 1 : fadeOut(frame, 90, 30);

  const stats: StatProps[] = [
    { value: "10×", label: "Faster delivery", delay: 10 },
    { value: "99.9%", label: "Uptime SLA", delay: 30 },
    { value: "∞", label: "Scalability", delay: 50 },
  ];

  return (
    <AbsoluteFill style={{ background: BRAND.bg, justifyContent: "center", alignItems: "center", flexDirection: "column", gap: 80, opacity: exitOpacity }}>
      <div style={{
        opacity: fadeIn(frame, 5, 20),
        fontSize: 36,
        color: BRAND.muted,
        fontFamily: "system-ui, sans-serif",
        letterSpacing: 4,
        textTransform: "uppercase",
      }}>
        Trusted by builders worldwide
      </div>

      <div style={{ display: "flex", gap: 80, alignItems: "center" }}>
        {stats.map((s) => (
          <StatBlock key={s.label} {...s} frame={frame} />
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 4: CTA / outro (frames 510 – 599, ~3 s) ────────────────
const SceneCTA: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgOpacity = fadeIn(frame, 0, 20);

  const logoScale = spring({ frame, fps, config: { damping: 20, stiffness: 100 }, durationInFrames: 40 });
  const ctaOpacity = fadeIn(frame, 35, 25);
  const urlOpacity = fadeIn(frame, 55, 20);

  return (
    <AbsoluteFill style={{
      background: BRAND.bg,
      justifyContent: "center",
      alignItems: "center",
      flexDirection: "column",
      gap: 32,
      opacity: bgOpacity,
    }}>
      {/* Full-screen gradient overlay */}
      <div style={{
        position: "absolute",
        inset: 0,
        background: `radial-gradient(ellipse at center, ${BRAND.primary}18 0%, transparent 65%)`,
        pointerEvents: "none",
      }} />

      {/* Logo mark */}
      <div style={{
        width: 96,
        height: 96,
        borderRadius: "50%",
        background: BRAND.gradient,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${logoScale})`,
        boxShadow: `0 0 80px ${BRAND.primary}88`,
      }}>
        <span style={{ fontSize: 36, fontWeight: 800, color: BRAND.white, fontFamily: "system-ui, sans-serif", letterSpacing: -1 }}>
          dk
        </span>
      </div>

      {/* CTA text */}
      <div style={{ opacity: ctaOpacity, textAlign: "center" }}>
        <div style={{
          fontSize: 52,
          fontWeight: 800,
          color: BRAND.white,
          fontFamily: "system-ui, sans-serif",
          letterSpacing: -2,
          lineHeight: 1.15,
        }}>
          Ready to build
          <br />
          <span style={{ background: BRAND.gradient, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            something great?
          </span>
        </div>
      </div>

      {/* URL / CTA badge */}
      <div style={{
        opacity: urlOpacity,
        background: BRAND.gradient,
        borderRadius: 50,
        padding: "14px 40px",
        marginTop: 8,
      }}>
        <span style={{
          fontSize: 22,
          fontWeight: 700,
          color: BRAND.white,
          fontFamily: "system-ui, sans-serif",
          letterSpacing: 1,
        }}>
          github.com/zhion008/dkapps
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ── Root composition: 20 s = 600 frames ──────────────────────────
export const BrandedIntro: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: BRAND.bg }}>
      {/* Scene 1 – Logo reveal: 0–179 */}
      <Sequence from={0} durationInFrames={180}>
        <SceneLogo />
      </Sequence>

      {/* Scene 2 – Features: 180–389 */}
      <Sequence from={180} durationInFrames={210}>
        <SceneFeatures />
      </Sequence>

      {/* Scene 3 – Stats: 390–509 */}
      <Sequence from={390} durationInFrames={120}>
        <SceneStats />
      </Sequence>

      {/* Scene 4 – CTA: 510–599 */}
      <Sequence from={510} durationInFrames={90}>
        <SceneCTA />
      </Sequence>
    </AbsoluteFill>
  );
};
