/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Government-dashboard palette: navy + saffron accents (India civic theme)
        gov: {
          50: '#f5f7fa',
          100: '#eaeef4',
          200: '#d1dae8',
          300: '#a9bad3',
          400: '#7b95b6',
          500: '#58789f',
          600: '#1e3a5f',
          700: '#16293f',
          800: '#0f1d2c',
          900: '#0a1420',
        },
        saffron: {
          400: '#ffa726',
          500: '#ff9800',
          600: '#f57c00',
        },
      },
    },
  },
  plugins: [],
}
