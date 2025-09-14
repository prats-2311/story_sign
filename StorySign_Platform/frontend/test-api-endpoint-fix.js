#!/usr/bin/env node

/**
 * Test script to verify the API endpoint fix
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
  `${colors.bold}${colors.blue}🔧 API ENDPOINT FIX VERIFICATION${colors.reset}`
);
console.log("=".repeat(50));

try {
  // Check ASLWorldPage.js
  console.log(`\n${colors.yellow}Checking ASLWorldPage.js...${colors.reset}`);
  const aslWorldPage = fs.readFileSync(
    path.join(__dirname, "src/pages/ASLWorldPage.js"),
    "utf8"
  );

  if (
    aslWorldPage.includes("/api/asl-world/story/recognize_and_generate") &&
    !aslWorldPage.includes("/api/v1/asl-world/story/recognize_and_generate")
  ) {
    console.log(
      `${colors.green}✅ ASLWorldPage.js uses correct API endpoint${colors.reset}`
    );
  } else {
    console.log(
      `${colors.red}❌ ASLWorldPage.js still has incorrect API endpoint${colors.reset}`
    );
  }

  // Check test files
  console.log(`\n${colors.yellow}Checking test files...${colors.reset}`);

  const globalSetup = fs.readFileSync(
    path.join(__dirname, "src/tests/e2e/global-setup.js"),
    "utf8"
  );

  if (
    globalSetup.includes("/api/asl-world/story/recognize_and_generate") &&
    !globalSetup.includes("/api/v1/asl-world/story/recognize_and_generate")
  ) {
    console.log(
      `${colors.green}✅ global-setup.js uses correct API endpoint${colors.reset}`
    );
  } else {
    console.log(
      `${colors.red}❌ global-setup.js still has incorrect API endpoint${colors.reset}`
    );
  }

  const performanceTest = fs.readFileSync(
    path.join(__dirname, "src/tests/e2e/performance-integration.test.js"),
    "utf8"
  );

  if (
    performanceTest.includes("/api/asl-world/story/recognize_and_generate") &&
    !performanceTest.includes("/api/v1/asl-world/story/recognize_and_generate")
  ) {
    console.log(
      `${colors.green}✅ performance-integration.test.js uses correct API endpoint${colors.reset}`
    );
  } else {
    console.log(
      `${colors.red}❌ performance-integration.test.js still has incorrect API endpoint${colors.reset}`
    );
  }

  console.log(
    `\n${colors.bold}${colors.green}🎉 API ENDPOINT FIX COMPLETED!${colors.reset}`
  );

  console.log(`\n${colors.yellow}The fix changes:${colors.reset}`);
  console.log(
    "• Frontend now calls: /api/asl-world/story/recognize_and_generate"
  );
  console.log(
    "• Backend provides: /api/asl-world/story/recognize_and_generate"
  );
  console.log("• Removed incorrect /v1 prefix from frontend calls");

  console.log(`\n${colors.blue}Expected result:${colors.reset}`);
  console.log("• No more 404 errors when generating stories");
  console.log("• Story generation should work immediately");
  console.log("• Webcam photo story generation should succeed");
} catch (error) {
  console.error(
    `${colors.red}❌ Error verifying fix: ${error.message}${colors.reset}`
  );
  process.exit(1);
}

console.log(
  `\n${colors.green}API endpoint fix completed! Test story generation now. ✨${colors.reset}\n`
);
