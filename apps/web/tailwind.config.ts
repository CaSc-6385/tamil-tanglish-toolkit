import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx,mdx}", "./components/**/*.{ts,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        // Kid-friendly defaults; Noto Sans Tamil added in globals.css via @import
        sans: ["system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        tamil: ["'Noto Sans Tamil'", "system-ui", "sans-serif"],
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
      },
      fontSize: {
        kid: ["1.375rem", { lineHeight: "1.8rem" }],
        "kid-lg": ["1.75rem", { lineHeight: "2.25rem" }],
      },
    },
  },
  plugins: [],
};

export default config;
