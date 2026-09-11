/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f4f9fd',
          100: '#e0eef9',
          200: '#b3d4ee',
          300: '#7fb4e0',
          400: '#4a93d1',
          500: '#2b76bd',
          600: '#1d5fa3',
          700: '#154a8a',
          800: '#0f3d75',
          900: '#0a2e5c',
          950: '#06182d',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
