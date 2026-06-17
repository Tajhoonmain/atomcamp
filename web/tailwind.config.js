/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0A0E1A",
        surface: "#12172A",
        surface2: "#171D33",
        border: "#222842",
        primary: "#4F46E5",
        primary2: "#6366F1",
        accent: "#2DD4BF",
        muted: "#8A90A6",
        ink2: "#0C1120",
      },
      fontFamily: {
        sora: ["Sora", "system-ui", "sans-serif"],
        inter: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(79,70,229,0.35)",
        glowteal: "0 0 36px rgba(45,212,191,0.30)",
      },
    },
  },
  plugins: [],
};
