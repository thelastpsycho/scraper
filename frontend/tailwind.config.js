/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'app-primary': '#F9FAFB',
        'app-secondary': '#F3F4F6',
        'app-tertiary': '#1F2937',
        'app-accent': '#3B82F6',
      },
    },
  },
  plugins: [],
}
