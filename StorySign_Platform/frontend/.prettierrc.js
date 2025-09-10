module.exports = {
  // Formatting options
  semi: true,
  trailingComma: "es5",
  singleQuote: false,
  doubleQuote: true,
  printWidth: 80,
  tabWidth: 2,
  useTabs: false,
  bracketSpacing: true,
  bracketSameLine: false,
  arrowParens: "avoid",
  endOfLine: "lf",

  // JSX specific options
  jsxSingleQuote: false,
  jsxBracketSameLine: false,

  // File-specific overrides
  overrides: [
    {
      files: "*.json",
      options: {
        printWidth: 120,
      },
    },
    {
      files: "*.md",
      options: {
        printWidth: 100,
        proseWrap: "always",
      },
    },
    {
      files: "*.css",
      options: {
        printWidth: 120,
      },
    },
  ],
};
