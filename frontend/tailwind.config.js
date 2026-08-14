/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Nunito Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['"Nunito Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      colors: {
        // Minimalist surfaces
        'app-primary': '#FFFFFF',    // card / surface
        'app-secondary': '#F1F5F9',  // subtle fill / hover (slate-100)
        'app-tertiary': '#0F172A',   // primary text (slate-900)
        'app-accent': '#0F172A',     // monochrome accent — actions / active
      },
      boxShadow: {
        // Flat, hairline definition (safety net so any leftover soft-UI class stays clean)
        neu: '0 0 0 1px rgb(226 232 240)',
        'neu-sm': '0 0 0 1px rgb(226 232 240)',
        'neu-inset': 'inset 0 0 0 1px rgb(226 232 240)',
        'neu-inset-sm': 'inset 0 0 0 1px rgb(226 232 240)',
        'neu-accent': '0 0 0 1px rgb(226 232 240)',
        xs: '0 1px 2px 0 rgb(15 23 42 / 0.04)',
      },
    },
  },
  plugins: [],
}
