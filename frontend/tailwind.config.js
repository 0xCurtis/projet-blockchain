/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          1: '#3772FF', // blue-500
          2: '#9757D7', // purple-500
          3: '#EF466F', // pink-500
          4: '#45B26B', // green-500
        },
        neutral: {
          1: '#141416',
          2: '#23262F', // black or gray-800
          3: '#353945',
          4: '#777E90', // gray-500
          5: '#B1B5C3', // gray-400
          6: '#E6E8EC', // gray-300 or gray-200
          7: '#F4F5F6', // gray-100
          8: '#FCFCFD', // white
        },
      },
      maxWidth: {
        '8xl': '90rem',
      },
    },
  },
  plugins: [],
};