/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Theme cam/kem lay cam hung tu VietDub (screenshot tham chieu).
        cream: "#FAF6F1",
        "cream-dark": "#F1E9DF",
        line: "#EDE4D8",
        ink: "#1F2937",
        "ink-soft": "#6B7280",
        primary: "#E8590C",
        "primary-soft": "#FFF0E5",
        "primary-hover": "#D9480F",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
