/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        outfit: ['Outfit', 'sans-serif'],
      },
      colors: {
        beige: {
          50: '#fdfbf7',   // Warm off-white
          100: '#f5efe6',  // Cream
          200: '#eadecc',  // Warm beige outline
          300: '#d2b48c',  // Muted tan
        },
        coffee: {
          500: '#8c6239',
          600: '#6f4e37',  // Primary coffee brown
          700: '#5a3d2a',
          800: '#3c2f2f',  // Primary dark espresso
          900: '#1e110e',  // Deep text dark espresso
        }
      }
    },
  },
  plugins: [],
}
