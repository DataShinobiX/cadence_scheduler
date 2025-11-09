/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      animation: {
        'fadeIn': 'fadeIn 0.5s ease-in-out',
        'slideDown': 'slideDown 0.4s ease-out',
        'slideUp': 'slideUp 0.4s ease-out',
        'slideInRight': 'slideInRight 0.3s ease-out',
        'soundWave': 'soundWave 0.8s ease-in-out infinite',
        'scaleIn': 'scaleIn 0.3s ease-out',
        'progress': 'progress 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideDown: {
          '0%': {
            opacity: '0',
            transform: 'translateY(-10px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        slideUp: {
          '0%': {
            opacity: '0',
            transform: 'translateY(10px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        slideInRight: {
          '0%': {
            opacity: '0',
            transform: 'translateX(100%)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateX(0)',
          },
        },
        soundWave: {
          '0%, 100%': {
            transform: 'scaleY(0.3)',
          },
          '50%': {
            transform: 'scaleY(1)',
          },
        },
        scaleIn: {
          '0%': {
            opacity: '0',
            transform: 'scale(0.9)',
          },
          '100%': {
            opacity: '1',
            transform: 'scale(1)',
          },
        },
        progress: {
          '0%': {
            width: '0%',
          },
          '50%': {
            width: '100%',
          },
          '100%': {
            width: '100%',
          },
        },
      },
    },
  },
  plugins: [],
};