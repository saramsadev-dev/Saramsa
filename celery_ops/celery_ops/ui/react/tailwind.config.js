/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Exact Trigger.dev colors
        'bg': '#0a0a0b',
        'bg-elevated': '#111113',
        'bg-sidebar': '#0a0a0b',
        'bg-hover': 'rgba(255,255,255,0.05)',
        'bg-row-hover': 'rgba(255,255,255,0.03)',
        'border': '#1f1f23',
        'border-subtle': '#18181b',
        'fg': '#fafafa',
        'fg-secondary': '#e4e4e7',
        'fg-muted': '#a1a1aa',
        'fg-dim': '#71717a',
        'accent': '#3b82f6',
        'accent-hover': '#60a5fa',
        'accent-bg': 'rgba(59,130,246,0.1)',
        'success': '#28bf5c',
        'success-bg': 'rgba(40,191,92,0.12)',
        'error': '#ef4444',
        'error-bg': 'rgba(239,68,68,0.12)',
        'warning': '#f59e0b',
        'warning-bg': 'rgba(245,158,11,0.12)',
        'purple': '#8b5cf6',
        'purple-bg': 'rgba(139,92,246,0.12)',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        'mono': ['SF Mono', 'Cascadia Code', 'Fira Code', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}