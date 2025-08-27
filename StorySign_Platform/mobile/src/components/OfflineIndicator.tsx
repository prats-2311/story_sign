import React from 'react';
import {View, Text, StyleSheet} from 'react-native';

export const OfflineIndicator: React.FC = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>📡 You're offline</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    backgroundColor: '#ff6b6b',
    paddingVertical: 8,
    paddingHorizontal: 16,
    zIndex: 1000,
  },
  text: {
    color: '#fff',
    textAlign: 'center',
    fontSize: 14,
    fontWeight: '600',
  },
});