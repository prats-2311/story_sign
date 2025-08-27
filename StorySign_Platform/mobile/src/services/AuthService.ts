import AsyncStorage from '@react-native-async-storage/async-storage';
import {Keychain} from 'react-native-keychain';

interface User {
  id: string;
  email: string;
  username: string;
  firstName: string;
  lastName: string;
  avatar?: string;
  preferences: any;
}

interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

class AuthServiceClass {
  private isInitialized = false;
  private currentUser: User | null = null;
  private tokens: AuthTokens | null = null;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Load stored tokens and user data
      await this.loadStoredAuth();
      
      // Validate tokens and refresh if needed
      if (this.tokens) {
        await this.validateAndRefreshTokens();
      }

      this.isInitialized = true;
      console.log('AuthService initialized successfully');
    } catch (error) {
      console.error('Failed to initialize AuthService:', error);
      throw error;
    }
  }

  private async loadStoredAuth(): Promise<void> {
    try {
      // Load tokens from secure storage
      const credentials = await Keychain.getInternetCredentials('storysign_tokens');
      if (credentials) {
        this.tokens = JSON.parse(credentials.password);
      }

      // Load user data from async storage
      const userData = await AsyncStorage.getItem('user_data');
      if (userData) {
        this.currentUser = JSON.parse(userData);
      }
    } catch (error) {
      console.error('Failed to load stored auth:', error);
    }
  }

  private async validateAndRefreshTokens(): Promise<boolean> {
    if (!this.tokens) return false;

    try {
      // Check if token is expired
      if (Date.now() >= this.tokens.expiresAt) {
        return await this.refreshTokens();
      }

      // Validate token with server
      const response = await fetch('/api/v1/auth/validate', {
        headers: {
          'Authorization': `Bearer ${this.tokens.accessToken}`,
        },
      });

      if (!response.ok) {
        return await this.refreshTokens();
      }

      return true;
    } catch (error) {
      console.error('Token validation failed:', error);
      return false;
    }
  }

  private async refreshTokens(): Promise<boolean> {
    if (!this.tokens?.refreshToken) return false;

    try {
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refreshToken: this.tokens.refreshToken,
        }),
      });

      if (!response.ok) {
        await this.logout();
        return false;
      }

      const data = await response.json();
      await this.storeTokens(data.accessToken, data.refreshToken, data.expiresIn);
      
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      await this.logout();
      return false;
    }
  }

  async login(email: string, password: string): Promise<User> {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({email, password}),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Login failed');
      }

      const data = await response.json();
      
      // Store tokens securely
      await this.storeTokens(data.accessToken, data.refreshToken, data.expiresIn);
      
      // Store user data
      this.currentUser = data.user;
      await AsyncStorage.setItem('user_data', JSON.stringify(data.user));

      return data.user;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  async register(userData: {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    username: string;
  }): Promise<User> {
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Registration failed');
      }

      const data = await response.json();
      
      // Store tokens securely
      await this.storeTokens(data.accessToken, data.refreshToken, data.expiresIn);
      
      // Store user data
      this.currentUser = data.user;
      await AsyncStorage.setItem('user_data', JSON.stringify(data.user));

      return data.user;
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      // Notify server of logout
      if (this.tokens?.accessToken) {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.tokens.accessToken}`,
          },
        });
      }
    } catch (error) {
      console.warn('Server logout failed:', error);
    } finally {
      // Clear local data
      await this.clearStoredAuth();
      this.currentUser = null;
      this.tokens = null;
    }
  }

  private async storeTokens(accessToken: string, refreshToken: string, expiresIn: number): Promise<void> {
    const tokens: AuthTokens = {
      accessToken,
      refreshToken,
      expiresAt: Date.now() + (expiresIn * 1000),
    };

    this.tokens = tokens;

    // Store in secure keychain
    await Keychain.setInternetCredentials(
      'storysign_tokens',
      'tokens',
      JSON.stringify(tokens)
    );
  }

  private async clearStoredAuth(): Promise<void> {
    try {
      await Keychain.resetInternetCredentials('storysign_tokens');
      await AsyncStorage.removeItem('user_data');
    } catch (error) {
      console.error('Failed to clear stored auth:', error);
    }
  }

  // Public getters
  getCurrentUser(): User | null {
    return this.currentUser;
  }

  getAccessToken(): string | null {
    return this.tokens?.accessToken || null;
  }

  isAuthenticated(): boolean {
    return !!(this.currentUser && this.tokens && Date.now() < this.tokens.expiresAt);
  }

  async updateProfile(updates: Partial<User>): Promise<User> {
    if (!this.currentUser || !this.tokens) {
      throw new Error('Not authenticated');
    }

    try {
      const response = await fetch('/api/v1/users/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.tokens.accessToken}`,
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Profile update failed');
      }

      const updatedUser = await response.json();
      this.currentUser = updatedUser;
      await AsyncStorage.setItem('user_data', JSON.stringify(updatedUser));

      return updatedUser;
    } catch (error) {
      console.error('Profile update failed:', error);
      throw error;
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    if (!this.tokens) {
      throw new Error('Not authenticated');
    }

    try {
      const response = await fetch('/api/v1/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.tokens.accessToken}`,
        },
        body: JSON.stringify({
          currentPassword,
          newPassword,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Password change failed');
      }
    } catch (error) {
      console.error('Password change failed:', error);
      throw error;
    }
  }

  async requestPasswordReset(email: string): Promise<void> {
    try {
      const response = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({email}),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Password reset request failed');
      }
    } catch (error) {
      console.error('Password reset request failed:', error);
      throw error;
    }
  }
}

export const AuthService = new AuthServiceClass();