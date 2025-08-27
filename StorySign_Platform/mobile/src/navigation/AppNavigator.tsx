import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {Platform} from 'react-native';

// Screens
import {HomeScreen} from '../screens/HomeScreen';
import {ASLWorldScreen} from '../screens/ASLWorldScreen';
import {ProgressScreen} from '../screens/ProgressScreen';
import {ProfileScreen} from '../screens/ProfileScreen';
import {SettingsScreen} from '../screens/SettingsScreen';
import {LoginScreen} from '../screens/LoginScreen';
import {OnboardingScreen} from '../screens/OnboardingScreen';
import {PracticeSessionScreen} from '../screens/PracticeSessionScreen';
import {StoryLibraryScreen} from '../screens/StoryLibraryScreen';

// Hooks
import {useAuth} from '../contexts/AuthContext';
import {useResponsive} from '../hooks/useResponsive';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

const TabNavigator = () => {
  const {isMobile} = useResponsive();
  
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#fff',
          borderTopWidth: 1,
          borderTopColor: '#e0e0e0',
          height: Platform.OS === 'ios' ? 90 : 70,
          paddingBottom: Platform.OS === 'ios' ? 30 : 10,
          paddingTop: 10,
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: '#8E8E93',
        tabBarLabelStyle: {
          fontSize: isMobile ? 12 : 14,
          fontWeight: '600',
        },
        tabBarIconStyle: {
          marginBottom: 4,
        },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({color, size}) => (
            <Text style={{fontSize: size, color}}>🏠</Text>
          ),
        }}
      />
      <Tab.Screen
        name="ASL World"
        component={ASLWorldScreen}
        options={{
          tabBarIcon: ({color, size}) => (
            <Text style={{fontSize: size, color}}>👋</Text>
          ),
        }}
      />
      <Tab.Screen
        name="Progress"
        component={ProgressScreen}
        options={{
          tabBarIcon: ({color, size}) => (
            <Text style={{fontSize: size, color}}>📊</Text>
          ),
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarIcon: ({color, size}) => (
            <Text style={{fontSize: size, color}}>👤</Text>
          ),
        }}
      />
    </Tab.Navigator>
  );
};

export const AppNavigator = () => {
  const {isAuthenticated, isLoading, hasCompletedOnboarding} = useAuth();

  if (isLoading) {
    return null; // Loading screen is handled in App.tsx
  }

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        gestureEnabled: true,
        cardStyleInterpolator: ({current, layouts}) => {
          return {
            cardStyle: {
              transform: [
                {
                  translateX: current.progress.interpolate({
                    inputRange: [0, 1],
                    outputRange: [layouts.screen.width, 0],
                  }),
                },
              ],
            },
          };
        },
      }}
    >
      {!isAuthenticated ? (
        <>
          {!hasCompletedOnboarding && (
            <Stack.Screen
              name="Onboarding"
              component={OnboardingScreen}
              options={{gestureEnabled: false}}
            />
          )}
          <Stack.Screen
            name="Login"
            component={LoginScreen}
            options={{gestureEnabled: false}}
          />
        </>
      ) : (
        <>
          <Stack.Screen name="Main" component={TabNavigator} />
          <Stack.Screen
            name="PracticeSession"
            component={PracticeSessionScreen}
            options={{
              headerShown: true,
              title: 'Practice Session',
              headerStyle: {
                backgroundColor: '#007AFF',
              },
              headerTintColor: '#fff',
              headerTitleStyle: {
                fontWeight: 'bold',
              },
            }}
          />
          <Stack.Screen
            name="StoryLibrary"
            component={StoryLibraryScreen}
            options={{
              headerShown: true,
              title: 'Story Library',
              headerStyle: {
                backgroundColor: '#007AFF',
              },
              headerTintColor: '#fff',
              headerTitleStyle: {
                fontWeight: 'bold',
              },
            }}
          />
          <Stack.Screen
            name="Settings"
            component={SettingsScreen}
            options={{
              headerShown: true,
              title: 'Settings',
              headerStyle: {
                backgroundColor: '#007AFF',
              },
              headerTintColor: '#fff',
              headerTitleStyle: {
                fontWeight: 'bold',
              },
            }}
          />
        </>
      )}
    </Stack.Navigator>
  );
};