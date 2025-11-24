/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#00ADB5',
        secondary: '#FFD369',
        dark: '#222831',
        darker: '#393E46',
      },
    },
  },
  plugins: [],
}
