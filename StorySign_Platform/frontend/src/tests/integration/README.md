# Integration Tests

This directory contains integration tests for the StorySign platform that verify complete user
workflows and system interactions.

## Test Structure

### `complete-user-workflow.test.js`

Comprehensive integration tests covering:

#### End-to-End Authentication Flow (Requirements 6.5, 6.6)

- Complete login to logout workflow
- Login error handling
- Logout error handling with graceful degradation

#### Protected Route Access and Redirection

- Unauthenticated users redirected to login from protected routes
- Authenticated users can access all protected routes
- Logout redirects to login from any protected route
- Authentication state maintained across route navigation

#### ASL World Functionality Without Manual Backend Connection

- Immediate access to ASL World without "Test Backend" button
- Webcam controls available immediately
- Story generation works without manual backend setup
- Seamless navigation from dashboard to ASL World
- Automatic backend connection status display

#### Complete User Journey Integration

- Full workflow: login → navigate → use features → logout
- Registration to login flow
- Multiple route navigation scenarios

#### Error Handling and Edge Cases

- Network error handling
- Token expiration during session
- Rapid navigation between routes

## Running Integration Tests

```bash
# Run integration tests only
npm run test:integration

# Run integration tests with coverage
npm run test:integration -- --coverage

# Run integration tests in watch mode
npm run test:integration -- --watch
```

## Test Configuration

- **Test Environment**: jsdom
- **Test Timeout**: 30 seconds
- **Max Workers**: 1 (serial execution for integration tests)
- **Coverage**: Collected from all source files except tests

## Mocked Dependencies

The integration tests mock complex dependencies to focus on workflow integration:

- **AuthService**: Mocked for controlled authentication state
- **Video Components**: Mocked to avoid WebRTC complexity
- **API Calls**: Mocked with fetch for predictable responses
- **Performance Utilities**: Mocked to avoid timing issues
- **Browser APIs**: localStorage, sessionStorage, WebSocket, etc.

## Test Utilities

Global test utilities are available in all integration tests:

- `testUtils.createMockUser()`: Creates mock user data
- `testUtils.createMockToken()`: Creates mock JWT token
- `testUtils.setupAuthenticatedState()`: Sets up authenticated state
- `testUtils.setupUnauthenticatedState()`: Sets up unauthenticated state
- `testUtils.waitForAsync()`: Helper for async operations

## Requirements Coverage

These integration tests verify the following requirements:

### Requirement 6.5: Complete user workflow verification

✅ End-to-end authentication flow with login and logout ✅ Protected route access and redirection
after logout ✅ Error handling throughout the user journey

### Requirement 6.6: ASL World immediate functionality

✅ ASL World functionality works immediately without "Test Backend" ✅ Story generation available
without manual backend connection ✅ Seamless navigation and feature access

## Test Scenarios

### Authentication Scenarios

1. **Successful Login Flow**: User logs in and accesses dashboard
2. **Login Error Handling**: Invalid credentials handled gracefully
3. **Logout Flow**: User logs out and is redirected to login
4. **Logout Error Handling**: Server errors don't prevent local logout

### Navigation Scenarios

1. **Protected Route Access**: Authenticated users can access all routes
2. **Unauthenticated Redirection**: Unauthenticated users redirected to login
3. **Post-Logout Redirection**: Users redirected to login after logout
4. **State Persistence**: Authentication state maintained across navigation

### Feature Access Scenarios

1. **Immediate ASL World Access**: No "Test Backend" button required
2. **Automatic Backend Connection**: Connection established automatically
3. **Feature Availability**: All features work immediately upon access
4. **Seamless Navigation**: Smooth transitions between modules

### Error Scenarios

1. **Network Errors**: App remains functional during network issues
2. **Token Expiration**: Graceful handling of expired authentication
3. **Rapid Navigation**: No errors during quick route changes
4. **Server Errors**: Graceful degradation when backend unavailable

## Success Criteria

All integration tests must pass to ensure:

1. **Authentication Flow**: Complete login/logout cycle works correctly
2. **Route Protection**: Proper access control for protected routes
3. **Feature Access**: Immediate functionality without manual setup
4. **Error Resilience**: Graceful handling of various error conditions
5. **User Experience**: Smooth and intuitive user workflows

## Maintenance

When adding new features or modifying existing workflows:

1. Update relevant test scenarios
2. Add new test cases for new user workflows
3. Update mocks if dependencies change
4. Ensure test coverage remains comprehensive
5. Update this documentation with new test scenarios
