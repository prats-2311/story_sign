/**
 * Manual Authentication Workflow Test Script
 * This script provides a simple way to manually test the authentication workflow
 * Run this in the browser console when the app is loaded
 */

window.testAuthWorkflow = {
  // Test data
  testUser: {
    username: "testuser123",
    email: "test@example.com",
    password: "TestPassword123!",
  },

  // Helper to wait for elements
  waitForElement: (selector, timeout = 5000) => {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const checkElement = () => {
        const element = document.querySelector(selector);
        if (element) {
          resolve(element);
        } else if (Date.now() - startTime > timeout) {
          reject(
            new Error(`Element ${selector} not found within ${timeout}ms`)
          );
        } else {
          setTimeout(checkElement, 100);
        }
      };
      checkElement();
    });
  },

  // Helper to simulate user input
  simulateInput: (element, value) => {
    element.focus();
    element.value = value;
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  },

  // Test 1: Verify unauthenticated redirect to login
  testUnauthenticatedRedirect: async () => {
    console.log("🧪 Testing unauthenticated redirect...");

    // Clear any existing auth data
    localStorage.clear();
    sessionStorage.clear();

    // Navigate to root
    window.location.href = "/";

    try {
      await testAuthWorkflow.waitForElement(
        'h1:contains("Sign In to StorySign")'
      );
      console.log("✅ Unauthenticated users correctly redirected to login");
      return true;
    } catch (error) {
      console.error("❌ Unauthenticated redirect test failed:", error);
      return false;
    }
  },

  // Test 2: Test login workflow
  testLoginWorkflow: async () => {
    console.log("🧪 Testing login workflow...");

    try {
      // Navigate to login page
      window.location.href = "/login";

      // Wait for login form
      const emailInput = await testAuthWorkflow.waitForElement(
        'input[name="email"]'
      );
      const passwordInput = await testAuthWorkflow.waitForElement(
        'input[name="password"]'
      );
      const submitButton = await testAuthWorkflow.waitForElement(
        'button[type="submit"]'
      );

      // Fill in form
      testAuthWorkflow.simulateInput(
        emailInput,
        testAuthWorkflow.testUser.email
      );
      testAuthWorkflow.simulateInput(
        passwordInput,
        testAuthWorkflow.testUser.password
      );

      console.log("📝 Login form filled with test credentials");
      console.log("⚠️  Note: This will attempt to login with mock credentials");
      console.log("   Click the submit button manually to test the login flow");

      return true;
    } catch (error) {
      console.error("❌ Login workflow test failed:", error);
      return false;
    }
  },

  // Test 3: Test registration workflow
  testRegistrationWorkflow: async () => {
    console.log("🧪 Testing registration workflow...");

    try {
      // Navigate to register page
      window.location.href = "/register";

      // Wait for registration form
      const usernameInput = await testAuthWorkflow.waitForElement(
        'input[name="username"]'
      );
      const emailInput = await testAuthWorkflow.waitForElement(
        'input[name="email"]'
      );
      const passwordInput = await testAuthWorkflow.waitForElement(
        'input[name="password"]'
      );
      const confirmPasswordInput = await testAuthWorkflow.waitForElement(
        'input[name="confirmPassword"]'
      );

      // Fill in form
      testAuthWorkflow.simulateInput(
        usernameInput,
        testAuthWorkflow.testUser.username
      );
      testAuthWorkflow.simulateInput(
        emailInput,
        testAuthWorkflow.testUser.email
      );
      testAuthWorkflow.simulateInput(
        passwordInput,
        testAuthWorkflow.testUser.password
      );
      testAuthWorkflow.simulateInput(
        confirmPasswordInput,
        testAuthWorkflow.testUser.password
      );

      console.log("📝 Registration form filled with test data");
      console.log(
        "⚠️  Note: This will attempt to register with mock credentials"
      );
      console.log(
        "   Click the submit button manually to test the registration flow"
      );

      return true;
    } catch (error) {
      console.error("❌ Registration workflow test failed:", error);
      return false;
    }
  },

  // Test 4: Test protected route access
  testProtectedRouteAccess: async () => {
    console.log("🧪 Testing protected route access...");

    const protectedRoutes = [
      "/dashboard",
      "/asl-world",
      "/harmony",
      "/reconnect",
    ];
    const results = [];

    for (const route of protectedRoutes) {
      try {
        console.log(`Testing route: ${route}`);
        window.location.href = route;

        // Wait a bit for redirect
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Check if we're on login page (redirect happened)
        const isOnLogin =
          window.location.pathname === "/login" ||
          document.querySelector('h1:contains("Sign In to StorySign")');

        if (isOnLogin) {
          console.log(`✅ ${route} correctly redirected to login`);
          results.push({ route, success: true });
        } else {
          console.log(`❌ ${route} did not redirect to login`);
          results.push({ route, success: false });
        }
      } catch (error) {
        console.error(`❌ Error testing ${route}:`, error);
        results.push({ route, success: false, error });
      }
    }

    return results;
  },

  // Test 5: Test navigation consistency
  testNavigationConsistency: async () => {
    console.log("🧪 Testing navigation consistency...");

    try {
      // This test assumes user is authenticated
      // Check if PlatformShell navigation is present
      const navElements = document.querySelectorAll(
        '[data-testid="platform-nav"] a'
      );

      if (navElements.length > 0) {
        console.log("✅ Platform navigation found");
        console.log(`Found ${navElements.length} navigation links:`);
        navElements.forEach(link => {
          console.log(`  - ${link.textContent}: ${link.href}`);
        });
        return true;
      } else {
        console.log("❌ Platform navigation not found");
        return false;
      }
    } catch (error) {
      console.error("❌ Navigation consistency test failed:", error);
      return false;
    }
  },

  // Run all tests
  runAllTests: async () => {
    console.log("🚀 Starting complete authentication workflow tests...");
    console.log("=".repeat(50));

    const results = {
      unauthenticatedRedirect:
        await testAuthWorkflow.testUnauthenticatedRedirect(),
      loginWorkflow: await testAuthWorkflow.testLoginWorkflow(),
      registrationWorkflow: await testAuthWorkflow.testRegistrationWorkflow(),
      protectedRouteAccess: await testAuthWorkflow.testProtectedRouteAccess(),
      navigationConsistency: await testAuthWorkflow.testNavigationConsistency(),
    };

    console.log("=".repeat(50));
    console.log("📊 Test Results Summary:");
    Object.entries(results).forEach(([test, result]) => {
      const status = Array.isArray(result)
        ? result.every(r => r.success)
          ? "✅"
          : "❌"
        : result
        ? "✅"
        : "❌";
      console.log(
        `${status} ${test}: ${
          Array.isArray(result) ? "See details above" : result
        }`
      );
    });

    return results;
  },

  // Helper to check current authentication state
  checkAuthState: () => {
    const token =
      localStorage.getItem("auth_token") ||
      sessionStorage.getItem("auth_token");
    const user =
      localStorage.getItem("auth_user") || sessionStorage.getItem("auth_user");

    console.log("🔍 Current Authentication State:");
    console.log(`Token: ${token ? "Present" : "Not found"}`);
    console.log(
      `User: ${user ? JSON.parse(user).email || "Present" : "Not found"}`
    );
    console.log(`Current path: ${window.location.pathname}`);

    return {
      hasToken: !!token,
      hasUser: !!user,
      currentPath: window.location.pathname,
    };
  },

  // Instructions for manual testing
  showInstructions: () => {
    console.log(`
🧪 Manual Authentication Workflow Testing

Available commands:
- testAuthWorkflow.runAllTests()           - Run all automated tests
- testAuthWorkflow.testUnauthenticatedRedirect() - Test redirect to login
- testAuthWorkflow.testLoginWorkflow()     - Test login form
- testAuthWorkflow.testRegistrationWorkflow() - Test registration form
- testAuthWorkflow.testProtectedRouteAccess() - Test protected routes
- testAuthWorkflow.testNavigationConsistency() - Test navigation
- testAuthWorkflow.checkAuthState()        - Check current auth state

Manual Test Steps:
1. Clear browser storage and refresh page
2. Verify redirect to login page
3. Try accessing protected routes directly
4. Test login with valid credentials
5. Test registration workflow
6. Verify navigation between modules
7. Test logout functionality

Note: Some tests require manual interaction (clicking buttons)
to complete the authentication flow.
    `);
  },
};

// Auto-show instructions when script loads
console.log("🧪 Manual Authentication Test Script Loaded");
testAuthWorkflow.showInstructions();
