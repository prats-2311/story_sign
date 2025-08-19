#!/usr/bin/env node

/**
 * Test script to verify end-to-end connectivity between frontend and backend
 * This simulates the frontend's fetch call to the backend health endpoint
 */

const https = require("https");
const http = require("http");

async function testBackendConnectivity() {
  console.log("Testing StorySign Backend Connectivity...\n");

  return new Promise((resolve, reject) => {
    const options = {
      hostname: "localhost",
      port: 8000,
      path: "/",
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    };

    const req = http.request(options, (res) => {
      let data = "";

      console.log(`Status Code: ${res.statusCode}`);
      console.log(`Headers:`, res.headers);

      res.on("data", (chunk) => {
        data += chunk;
      });

      res.on("end", () => {
        try {
          const jsonData = JSON.parse(data);
          console.log("\n✅ Backend Response:");
          console.log(JSON.stringify(jsonData, null, 2));

          // Verify expected response structure
          if (jsonData.message && jsonData.status === "healthy") {
            console.log("\n✅ Backend connectivity test PASSED");
            console.log("✅ Response contains expected message and status");
            console.log("✅ End-to-end connectivity verified");
            resolve(true);
          } else {
            console.log("\n❌ Backend response missing expected fields");
            resolve(false);
          }
        } catch (error) {
          console.log("\n❌ Failed to parse JSON response:", error.message);
          resolve(false);
        }
      });
    });

    req.on("error", (error) => {
      console.log("\n❌ Connection failed:", error.message);
      console.log("❌ Make sure the backend server is running on port 8000");
      resolve(false);
    });

    req.setTimeout(5000, () => {
      console.log("\n❌ Request timeout");
      req.destroy();
      resolve(false);
    });

    req.end();
  });
}

async function testFrontendAvailability() {
  console.log("\nTesting Frontend Availability...\n");

  return new Promise((resolve, reject) => {
    const options = {
      hostname: "localhost",
      port: 3000,
      path: "/",
      method: "GET",
    };

    const req = http.request(options, (res) => {
      console.log(`Frontend Status Code: ${res.statusCode}`);

      if (res.statusCode === 200) {
        console.log("✅ Frontend is accessible on port 3000");
        resolve(true);
      } else {
        console.log("❌ Frontend returned unexpected status code");
        resolve(false);
      }
    });

    req.on("error", (error) => {
      console.log("❌ Frontend connection failed:", error.message);
      console.log("❌ Make sure the React dev server is running on port 3000");
      resolve(false);
    });

    req.setTimeout(5000, () => {
      console.log("❌ Frontend request timeout");
      req.destroy();
      resolve(false);
    });

    req.end();
  });
}

async function runTests() {
  console.log("=".repeat(60));
  console.log("StorySign Platform - End-to-End Connectivity Test");
  console.log("=".repeat(60));

  const frontendOk = await testFrontendAvailability();
  const backendOk = await testBackendConnectivity();

  console.log("\n" + "=".repeat(60));
  console.log("TEST SUMMARY");
  console.log("=".repeat(60));
  console.log(`Frontend (React): ${frontendOk ? "✅ PASS" : "❌ FAIL"}`);
  console.log(`Backend (FastAPI): ${backendOk ? "✅ PASS" : "❌ FAIL"}`);
  console.log(`Overall: ${frontendOk && backendOk ? "✅ PASS" : "❌ FAIL"}`);

  if (frontendOk && backendOk) {
    console.log("\n🎉 All systems operational! You can now:");
    console.log("   1. Open http://localhost:3000 in your browser");
    console.log('   2. Click the "Test Backend" button to verify connectivity');
    console.log("   3. See the backend response in the message area");
  } else {
    console.log("\n⚠️  Some services are not running. Please check:");
    if (!frontendOk)
      console.log(
        "   - Start frontend: cd StorySign_Platform/frontend && npm start"
      );
    if (!backendOk)
      console.log(
        "   - Start backend: cd StorySign_Platform/backend && python main.py"
      );
  }

  process.exit(frontendOk && backendOk ? 0 : 1);
}

runTests().catch(console.error);
