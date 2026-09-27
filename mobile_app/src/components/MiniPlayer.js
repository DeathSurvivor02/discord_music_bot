import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { useAudio } from '../context/AudioContext';

export const MiniPlayer = ({ onExpand }) => {
  const {
    currentTrack,
    isPlaying,
    isLoadingTrack,
    isDJSpeaking,
    togglePlayPause,
    skipNext,
    positionMillis,
    durationMillis,
  } = useAudio();

  if (!currentTrack && !isLoadingTrack && !isDJSpeaking) {
    return null;
  }

  const progress = durationMillis > 0 ? (positionMillis / durationMillis) * 100 : 0;
  const title = currentTrack ? currentTrack.title : (isDJSpeaking ? 'DJ X Speaking...' : 'Loading...');
  const thumb = currentTrack?.thumbnail;

  return (
    <TouchableOpacity activeOpacity={0.9} style={styles.container} onPress={onExpand}>
      {/* Progress line */}
      <View style={styles.progressTrack}>
        <View style={[styles.progressBar, { width: `${Math.min(100, Math.max(0, progress))}%` }]} />
      </View>

      <View style={styles.content}>
        {thumb ? (
          <Image source={{ uri: thumb }} style={styles.thumbnail} />
        ) : (
          <View style={[styles.thumbnail, styles.thumbPlaceholder]}>
            <MaterialCommunityIcons
              name={isDJSpeaking ? "radio-tower" : "music-note"}
              size={24}
              color="#1DB954"
            />
          </View>
        )}

        <View style={styles.info}>
          <Text style={styles.title} numberOfLines={1}>
            {isDJSpeaking ? 'DJ X Commentary' : title}
          </Text>
          <Text style={styles.status} numberOfLines={1}>
            {isDJSpeaking ? 'Introducing next track...' : (isPlaying ? 'Playing on Mobile' : 'Paused')}
          </Text>
        </View>

        <View style={styles.controls}>
          {isLoadingTrack ? (
            <ActivityIndicator size="small" color="#1DB954" style={styles.controlBtn} />
          ) : (
            <TouchableOpacity onPress={togglePlayPause} style={styles.controlBtn}>
              <Ionicons
                name={isPlaying ? 'pause' : 'play'}
                size={26}
                color="#ffffff"
              />
            </TouchableOpacity>
          )}

          <TouchableOpacity onPress={skipNext} style={styles.controlBtn}>
            <Ionicons name="play-skip-forward" size={24} color="#b3b3b3" />
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#282828',
    borderTopLeftRadius: 10,
    borderTopRightRadius: 10,
    overflow: 'hidden',
    borderBottomWidth: 1,
    borderBottomColor: '#121212',
  },
  progressTrack: {
    height: 2.5,
    backgroundColor: '#3e3e3e',
    width: '100%',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#1DB954',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  thumbnail: {
    width: 44,
    height: 44,
    borderRadius: 6,
    backgroundColor: '#333333',
  },
  thumbPlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  info: {
    flex: 1,
    marginHorizontal: 12,
  },
  title: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  status: {
    color: '#b3b3b3',
    fontSize: 12,
    marginTop: 2,
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  controlBtn: {
    padding: 6,
    marginLeft: 6,
  },
});
