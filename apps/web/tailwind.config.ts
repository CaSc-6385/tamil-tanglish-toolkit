import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx,mdx}", "./components/**/*.{ts,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        // Loaded via next/font in app/layout.tsx (CSS variables).
        sans: ["var(--font-sans)", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        tamil: ["var(--font-tamil)", "var(--font-sans)", "system-ui", "sans-serif"],
      },
      colors: {
        aost: {
          50: "#fff8ea",
          100: "#feefd1",
          200: "#fcdc9b",
          300: "#fac661",
          400: "#f7ae35",
          500: "#f19014",
          600: "#d6700c",
          700: "#b1520d",
          800: "#904112",
          900: "#763612",
        },
        // Dark-surface helpers used across the UI.
        ink: {
          900: "#090b12",
          800: "#11141d",
          700: "#161a26",
          600: "#1d2230",
        },
      },
      fontSize: {
        kid: ["1.375rem", { lineHeight: "1.8rem" }],
        "kid-lg": ["1.9rem", { lineHeight: "2.5rem" }],
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "none" },
        },
        "pop-in": {
          "0%": { opacity: "0", transform: "translateY(8px) scale(0.98)", filter: "blur(4px)" },
          "100%": { opacity: "1", transform: "none", filter: "blur(0)" },
        },
        "pulse-dot": {
          "0%": { boxShadow: "0 0 0 0 rgba(247,174,53,0.5)" },
          "70%": { boxShadow: "0 0 0 9px rgba(247,174,53,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(247,174,53,0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.6s cubic-bezier(0.22,1,0.36,1) both",
        "pop-in": "pop-in 0.5s cubic-bezier(0.22,1,0.36,1) both",
        "pulse-dot": "pulse-dot 2s ease-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
