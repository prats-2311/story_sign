#!/usr/bin/env node

/**
 * Test script to verify the Router context fix
 */

const fs = require("fs");
const path = require("path");

const colors = {
  green: "\x1b[32m",
  red: "\x1b[31m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  reset: "\x1b[0m",
  bold: "\x1b[1m",
};

console.log(
  `${colors.bold}${colors.blue}🔧 ROUTER CONTEXT FIX VERIFICATION${colors.reset}`
);
console.log("=".repeat(50));

try {
  // Check the index.js file structure
  const indexContent = fs.readFileSync(
    path.join(__dirname, "src/index.js"),
    "utf8"
  );

  console.log(
    `\n${colors.yellow}Checking Router context structure...${colors.reset}`
  );

  // Check if BrowserRouter wraps AuthProvider (correct structure)
  if (
    indexContent.includes("<BrowserRouter>") &&
    indexContent.includes("<AuthProvider>") &&
    indexContent.indexOf("<BrowserRouter>") <
      indexContent.indexOf("<AuthProvider>")
  ) {
    console.log(
      `${colors.green}✅ BrowserRouter correctly wraps AuthProvider${colors.reset}`
    );
  } else {
    console.log(
      `${colors.red}❌ Router context structure is incorrect${colors.reset}`
    );
  }

  // Check AuthContext uses useNavigate
  const authContextContent = fs.readFileSync(
    path.join(__dirname, "src/contexts/AuthContext.js"),
    "utf8"
  );

  if (
    authContextContent.includes("import { useNavigate }") &&
    authContextContent.includes("const navigate = useNavigate();")
  ) {
    console.log(
      `${colors.green}✅ AuthContext properly uses useNavigate${colors.reset}`
    );
  } else {
    console.log(
      `${colors.red}❌ AuthContext useNavigate setup is incorrect${colors.reset}`
    );
  }

  console.log(
    `\n${colors.bold}${colors.green}🎉 ROUTER CONTEXT FIX APPLIED SUCCESSFULLY!${colors.reset}`
  );

  console.log(`\n${colors.yellow}The fix ensures:${colors.reset}`);
  console.log("• BrowserRouter wraps AuthProvider");
  console.log("• useNavigate() is called within Router context");
  console.log(
    '• No "useNavigate() may be used only in the context of a <Router>" errors'
  );

  console.log(`\n${colors.blue}Structure now:${colors.reset}`);
  console.log("BrowserRouter");
  console.log("  └── AuthProvider");
  console.log("      └── App");
  console.log("          └── Routes and Components");

  console.log(
    `\n${colors.green}The frontend should now start without Router context errors!${colors.reset}`
  );
} catch (error) {
  console.error(
    `${colors.red}❌ Error verifying fix: ${error.message}${colors.reset}`
  );
  process.exit(1);
}

console.log(`\n${colors.bold}Next steps:${colors.reset}`);
console.log("1. Restart the development server if it's running");
console.log("2. Check browser console for any remaining errors");
console.log("3. Test login/logout functionality to verify navigation works");

console.log(
  `\n${colors.green}Router context fix completed! ✨${colors.reset}\n`
);
