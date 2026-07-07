import js from "@eslint/js";

export default [
  { ignores: ["dist/"] },
  js.configs.recommended,
  {
    rules: {
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
    },
    languageOptions: {
      globals: {
        document: "readonly",
        navigator: "readonly",
        window: "readonly",
        crypto: "readonly",
        setTimeout: "readonly",
        console: "readonly",
        fetch: "readonly",
        sessionStorage: "readonly",
        RequestInit: "readonly",
      },
    },
  },
];
