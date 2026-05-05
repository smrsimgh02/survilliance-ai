/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'sidebar-bg': '#0f172a',
        'main-bg': '#020617',
        'primary-accent': '#3b82f6',
        'danger-red': '#f43f5e',
      }
    },
  },
  plugins: [],
}
