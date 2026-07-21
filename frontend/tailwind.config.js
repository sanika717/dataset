/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Referenced throughout as bg-primary/text-primary/bg-danger/etc.
        // across every page and component built in this project — tune
        // these to your actual brand colors.
        primary: {
          DEFAULT: "#2563eb",
          50: "#eff6ff",
          100: "#dbeafe",
        },
        danger: {
          DEFAULT: "#dc2626",
        },
      },
    },
  },
  plugins: [],
};
