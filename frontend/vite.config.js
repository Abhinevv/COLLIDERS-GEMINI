import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: true, // listen on all network interfaces (including localhost)
    port: 5173
  },
  esbuild: {
    jsxInject: `import React from 'react'`,
  },
})
