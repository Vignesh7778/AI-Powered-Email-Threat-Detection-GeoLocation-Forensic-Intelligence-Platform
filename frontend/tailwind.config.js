/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        cyber: {
          dark: '#0b1120',
          panel: '#0f172a',
          card: '#1e293b',
          border: '#334155',
          cyan: '#38bdf8',
          blue: '#2563eb',
          emerald: '#10b981',
          crimson: '#ef4444',
          amber: '#f59e0b',
          purple: '#a855f7'
        }
      }
    },
  },
  plugins: [],
}
