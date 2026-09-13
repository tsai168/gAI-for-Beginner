// I03 addendum, ADR-0022/ADR-0025 §4: ESLint was deferred at B10 for a purely
// environmental reason (no Node.js in the implementation sandbox — see
// ADR-0022), not a decision gap. This config is written by hand against the
// same ESLint 9 flat-config + typescript-eslint + react-hooks/react-refresh
// pattern the Vite React-TS template ships, matching tsconfig.json's
// strict/ES2020/react-jsx settings. It has NOT been run — no Node.js/npm is
// available to install eslint or execute it. Verify with `npm run lint`
// once a Node.js environment is available; treat any rule mismatch found
// then as an environment-discovery fix, not a design change.
import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
    },
  },
);
