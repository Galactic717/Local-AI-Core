/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        codex: {
          bg: "#09090b",
          panel: "#161b22",
          border: "#30363d",
          text: "#c9d1d9",
          accent: "#58a6ff",
          cyan: "#00f5ff",
          purple: "#bc8cff"
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
