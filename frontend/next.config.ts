import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    // `msw/browser` resolves to `null` under the Node condition, which breaks
    // the SSR graph. Point every graph at the browser build instead.
    resolveAlias: {
      "msw/browser": "./node_modules/msw/lib/browser/index.js",
    },
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
