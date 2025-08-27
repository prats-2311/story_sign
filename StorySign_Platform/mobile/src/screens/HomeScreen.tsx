import React from 'react';
import {View, Text, StyleSheet, ScrollView, TouchableOpacity} from 'react-native';
import {useNavigation} from '@react-navigation/native';
import {useAuth} from '../contexts/AuthContext';
import {useDevice} from '../contexts/DeviceContext';

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation();
  const {user} = useAuth();
  const {deviceInfo, isOnline} = useDevice();

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Welcome to StorySign</Text>
        <Text style={styles.subtitle}>
          {user ? `Hello, ${user.firstName}!` : 'Start your ASL journey'}
        </Text>
      </View>

      <View style={styles.quickActions}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => navigation.navigate('ASL World' as never)}
        >
          <Text style={styles.actionIcon}>👋</Text>
          <Text style={styles.actionText}>Start Practice</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => navigation.navigate('StoryLibrary' as never)}
        >
          <Text style={styles.actionIcon}>📚</Text>
          <Text style={styles.actionText}>Story Library</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => navigation.navigate('Progress' as never)}
        >
          <Text style={styles.actionIcon}>📊</Text>
          <Text style={styles.actionText}>My Progress</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.deviceInfo}>
        <Text style={styles.sectionTitle}>Device Status</Text>
        <Text style={styles.infoText}>
          Device: {deviceInfo.deviceType} ({deviceInfo.platform})
        </Text>
        <Text style={styles.infoText}>
          Network: {isOnline ? 'Connected' : 'Offline'}
        </Text>
        <Text style={styles.infoText}>
          Camera: {deviceInfo.capabilities.hasCamera ? 'Available' : 'Not available'}
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#007AFF',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.9,
  },
  quickActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 20,
    justifyContent: 'space-between',
  },
  actionButton: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    width: '48%',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  actionText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  deviceInfo: {
    margin: 20,
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#333',
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
});