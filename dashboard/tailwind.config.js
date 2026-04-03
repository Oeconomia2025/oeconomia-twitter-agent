/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#111827",
          light: "#1f2937",
        },
        accent: {
          DEFAULT: "#00d4ff",
          dim: "#00d4ff33",
        },
        background: "#0b1016",
      },
    },
  },
  plugins: [],
};
