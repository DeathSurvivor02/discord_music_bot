import React, { useState, useEffect } from 'react';
import { View, StyleSheet, BackHandler } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { AudioProvider } from './src/context/AudioContext';
import { HomeScreen } from './src/screens/HomeScreen';
import { PlayerScreen } from './src/screens/PlayerScreen';
import { QueueScreen } from './src/screens/QueueScreen';
import { MiniPlayer } from './src/components/MiniPlayer';

function MainNavigator() {
  const [activeScreen, setActiveScreen] = useState('home'); // 'home' | 'player' | 'queue'

  useEffect(() => {
    const onBackPress = () => {
      if (activeScreen === 'queue') {
        setActiveScreen('player');
        return true;
      }
      if (activeScreen === 'player') {
        setActiveScreen('home');
        return true;
      }
      return false;
    };

    const sub = BackHandler.addEventListener('hardwareBackPress', onBackPress);
    return () => sub.remove();
  }, [activeScreen]);

  return (
    <View style={styles.container}>
      <StatusBar style="light" backgroundColor="#121212" />

      {activeScreen === 'home' && (
        <View style={styles.screenWrapper}>
          <HomeScreen onOpenPlayer={() => setActiveScreen('player')} />
          <MiniPlayer onExpand={() => setActiveScreen('player')} />
        </View>
      )}

      {activeScreen === 'player' && (
        <PlayerScreen
          onMinimize={() => setActiveScreen('home')}
          onOpenQueue={() => setActiveScreen('queue')}
        />
      )}

      {activeScreen === 'queue' && (
        <QueueScreen onClose={() => setActiveScreen('player')} />
      )}
    </View>
  );
}

export default function App() {
  return (
    <AudioProvider>
      <MainNavigator />
    </AudioProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  screenWrapper: {
    flex: 1,
    backgroundColor: '#121212',
    justifyContent: 'space-between',
  },
});
