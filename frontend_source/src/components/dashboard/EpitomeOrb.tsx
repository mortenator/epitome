/**
 * EpitomeOrb — A dark-mode-native animated orb.
 * Inspired by ElevenLabs: layered gradients, subtle rotation, and a soft pulsing glow.
 * Works against dark backgrounds without any white/blue artifacts.
 */
export function EpitomeOrb({ size = 112 }: { size?: number }) {
  return (
    <div
      style={{ width: size, height: size, position: "relative" }}
      className="flex items-center justify-center"
    >
      {/* Outer glow ring */}
      <div
        className="absolute inset-0 rounded-full opacity-30 animate-pulse"
        style={{
          background:
            "radial-gradient(circle at center, hsla(172, 49%, 42%, 0.6) 0%, transparent 70%)",
          filter: "blur(16px)",
          transform: "scale(1.4)",
        }}
      />

      {/* Main orb body */}
      <div
        className="absolute inset-0 rounded-full overflow-hidden"
        style={{
          background:
            "radial-gradient(circle at 38% 35%, #2a9a8a 0%, #1a6a62 30%, #0d3d3a 60%, #081e1e 100%)",
          boxShadow:
            "inset 0 0 40px 8px rgba(45, 140, 126, 0.25), 0 0 40px 8px rgba(45, 140, 126, 0.15)",
        }}
      >
        {/* Inner swirl layer 1 */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background:
              "conic-gradient(from 0deg at 40% 45%, transparent 0deg, rgba(45, 140, 126, 0.4) 60deg, transparent 120deg, rgba(80, 200, 180, 0.2) 200deg, transparent 280deg, rgba(45, 140, 126, 0.3) 340deg, transparent 360deg)",
            animation: "orb-rotate 8s linear infinite",
            mixBlendMode: "screen",
          }}
        />

        {/* Inner swirl layer 2 (counter-rotate for depth) */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background:
              "conic-gradient(from 180deg at 60% 55%, transparent 0deg, rgba(100, 220, 200, 0.15) 80deg, transparent 160deg, rgba(45, 140, 126, 0.25) 240deg, transparent 320deg)",
            animation: "orb-rotate-reverse 12s linear infinite",
            mixBlendMode: "screen",
          }}
        />

        {/* Highlight spec (top-left sheen) */}
        <div
          className="absolute rounded-full"
          style={{
            top: "12%",
            left: "14%",
            width: "35%",
            height: "25%",
            background:
              "radial-gradient(ellipse at center, rgba(255,255,255,0.18) 0%, transparent 70%)",
            filter: "blur(3px)",
            transform: "rotate(-30deg)",
          }}
        />
      </div>

      {/* CSS for the rotation animations */}
      <style>{`
        @keyframes orb-rotate {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @keyframes orb-rotate-reverse {
          from { transform: rotate(0deg); }
          to   { transform: rotate(-360deg); }
        }
      `}</style>
    </div>
  );
}
