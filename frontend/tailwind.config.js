/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: '#0B132B',      // Deep background
          blue: '#1C2541',      // Card background
          indigo: '#3A506B',    // Secondary
          teal: '#5BC0BE',      // Accent / Highlighting
          gold: '#FFD700',      // Brand yellow / Warning
        },
        severity: {
          low: '#10B981',       // Emerald Green
          medium: '#F59E0B',    // Amber Yellow
          high: '#F97316',      // Orange
          critical: '#EF4444'   // Red
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'premium': '0 10px 40px -10px rgba(0,0,0,0.5)',
      }
    },
  },
  plugins: [],
}
