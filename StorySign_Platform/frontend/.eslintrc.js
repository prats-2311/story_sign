module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true,
    jest: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:jsx-a11y/recommended",
    "plugin:import/recommended",
    "plugin:import/errors",
    "plugin:import/warnings",
  ],
  plugins: ["react", "react-hooks", "jsx-a11y", "import"],
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 2021,
    sourceType: "module",
  },
  settings: {
    react: {
      version: "detect",
    },
    "import/resolver": {
      node: {
        extensions: [".js", ".jsx", ".ts", ".tsx"],
      },
    },
  },
  rules: {
    // React specific rules
    "react/react-in-jsx-scope": "off", // Not needed in React 17+
    "react/prop-types": "warn",
    "react/no-unused-prop-types": "warn",
    "react/jsx-uses-react": "off", // Not needed in React 17+
    "react/jsx-uses-vars": "error",
    "react/jsx-key": "error",
    "react/jsx-no-duplicate-props": "error",
    "react/jsx-no-undef": "error",
    "react/jsx-pascal-case": "error",
    "react/no-direct-mutation-state": "error",
    "react/no-typos": "error",
    "react/require-render-return": "error",

    // React Hooks rules
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn",

    // Accessibility rules
    "jsx-a11y/anchor-is-valid": "error",
    "jsx-a11y/alt-text": "error",
    "jsx-a11y/aria-props": "error",
    "jsx-a11y/aria-proptypes": "error",
    "jsx-a11y/aria-unsupported-elements": "error",
    "jsx-a11y/role-has-required-aria-props": "error",
    "jsx-a11y/role-supports-aria-props": "error",
    "jsx-a11y/tabindex-no-positive": "error",
    "jsx-a11y/heading-has-content": "error",
    "jsx-a11y/html-has-lang": "error",
    "jsx-a11y/lang": "error",
    "jsx-a11y/no-distracting-elements": "error",
    "jsx-a11y/no-redundant-roles": "error",
    "jsx-a11y/click-events-have-key-events": "error",
    "jsx-a11y/no-static-element-interactions": "error",
    "jsx-a11y/interactive-supports-focus": "error",

    // Import rules
    "import/no-unresolved": "error",
    "import/named": "error",
    "import/default": "error",
    "import/namespace": "error",
    "import/no-absolute-path": "error",
    "import/no-dynamic-require": "error",
    "import/no-self-import": "error",
    "import/no-cycle": "error",
    "import/no-useless-path-segments": "error",
    "import/order": [
      "error",
      {
        groups: [
          "builtin",
          "external",
          "internal",
          "parent",
          "sibling",
          "index",
        ],
        "newlines-between": "always",
        alphabetize: {
          order: "asc",
          caseInsensitive: true,
        },
      },
    ],

    // General JavaScript rules
    "no-console": process.env.NODE_ENV === "production" ? "error" : "warn",
    "no-debugger": process.env.NODE_ENV === "production" ? "error" : "warn",
    "no-unused-vars": [
      "error",
      {
        vars: "all",
        args: "after-used",
        ignoreRestSiblings: true,
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
      },
    ],
    "no-var": "error",
    "prefer-const": "error",
    "prefer-arrow-callback": "error",
    "arrow-spacing": "error",
    "no-duplicate-imports": "error",
    "no-useless-constructor": "error",
    "no-useless-rename": "error",
    "object-shorthand": "error",
    "prefer-destructuring": [
      "error",
      {
        array: false,
        object: true,
      },
    ],
    "prefer-template": "error",
    "template-curly-spacing": "error",
    "yield-star-spacing": "error",

    // Code quality rules
    complexity: ["warn", 10],
    "max-depth": ["warn", 4],
    "max-lines": ["warn", 300],
    "max-lines-per-function": ["warn", 50],
    "max-params": ["warn", 4],
    "no-magic-numbers": [
      "warn",
      {
        ignore: [-1, 0, 1, 2],
        ignoreArrayIndexes: true,
        enforceConst: true,
      },
    ],

    // Performance rules
    "no-await-in-loop": "warn",
    "no-inner-declarations": "error",
    "no-loop-func": "error",

    // Security rules
    "no-eval": "error",
    "no-implied-eval": "error",
    "no-new-func": "error",
    "no-script-url": "error",
  },
  overrides: [
    {
      files: ["**/*.test.js", "**/*.test.jsx", "**/*.spec.js", "**/*.spec.jsx"],
      env: {
        jest: true,
      },
      extends: ["plugin:testing-library/react"],
      plugins: ["testing-library"],
      rules: {
        // Allow console in tests
        "no-console": "off",
        // Allow magic numbers in tests
        "no-magic-numbers": "off",
        // Testing library specific rules
        "testing-library/await-async-query": "error",
        "testing-library/no-await-sync-query": "error",
        "testing-library/no-debug": "warn",
        "testing-library/no-dom-import": "error",
        "testing-library/prefer-screen-queries": "error",
      },
    },
    {
      files: ["src/setupTests.js", "src/test-utils.js"],
      rules: {
        "import/no-extraneous-dependencies": "off",
      },
    },
  ],
};
