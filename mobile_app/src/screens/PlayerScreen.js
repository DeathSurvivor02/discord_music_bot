import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons, FontAwesome5 } from '@expo/vector-icons';
import { useAudio } from '../context/AudioContext';
import { DJVisualizer } from '../components/DJVisualizer';

const { width } = Dimensions.get('window');
const ARTWORK_SIZE = width - 72;

export const PlayerScreen = ({ onMinimize, onOpenQueue }) => {
  const {
    currentTrack,
    isPlaying,
    isLoadingTrack,
    isDJSpeaking,
    djSubtitle,
    positionMillis,
    durationMillis,
    isAutoplayEnabled,
    isDJEnabled,
    currentVibe,
    togglePlayPause,
    seekTo,
    skipNext,
    skipPrevious,
    toggleAutoplay,
    toggleDJ,
  } = useAudio();

  const [isSeeking, setIsSeeking] = useState(false);
  const [seekPos, setSeekPos] = useState(0);

  const formatTime = (millis) => {
    if (!millis || isNaN(millis)) return '0:00';
    const totalSec = Math.floor(millis / 1000);
    const min = Math.floor(totalSec / 60);
    const sec = totalSec % 60;
    return `${min}:${sec < 10 ? '0' : ''}${sec}`;
  };

  const progress = durationMillis > 0
    ? ((isSeeking ? seekPos : positionMillis) / durationMillis) * 100
    : 0;

  // Split title and artist
  let songName = currentTrack ? currentTrack.title : 'No Track Playing';
  let artistName = 'Spotify AI DJ Session';
  if (currentTrack && currentTrack.title && currentTrack.title.includes(' - ')) {
    const parts = currentTrack.title.split(' - ');
    songName = parts[0].trim();
    artistName = parts.slice(1).join(' - ').trim();
  }

  const thumbUri = currentTrack?.thumbnail;

  return (
    <View style={styles.container}>
      {/* Top Bar */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={onMinimize} style={styles.topBarBtn}>
          <Ionicons name="chevron-down" size={30} color="#ffffff" />
        </TouchableOpacity>

        <View style={styles.topBarCenter}>
          <Text style={styles.stationLabel}>PLAYING FROM VIBE</Text>
          <Text style={styles.stationName} numberOfLines={1}>{currentVibe.toUpperCase()}</Text>
        </View>

        <TouchableOpacity onPress={onOpenQueue} style={styles.topBarBtn}>
          <MaterialCommunityIcons name="playlist-music" size={28} color="#ffffff" />
        </TouchableOpacity>
      </View>

      {/* Album Artwork & DJ Overlay */}
      <View style={styles.artworkContainer}>
        <View style={[styles.artworkWrapper, isDJSpeaking && styles.artworkSpeakingBorder]}>
          {thumbUri ? (
            <Image source={{ uri: thumbUri }} style={styles.artwork} resizeMode="cover" />
          ) : (
            <View style={[styles.artwork, styles.artworkPlaceholder]}>
              <MaterialCommunityIcons name="radio-tower" size={80} color="#1DB954" />
            </View>
          )}

          {isDJSpeaking && (
            <View style={styles.djSpeakingOverlay}>
              <MaterialCommunityIcons name="microphone-variant" size={48} color="#1DB954" />
              <Text style={styles.djSpeakingText}>DJ X RADIO DROP</Text>
            </View>
          )}
        </View>
      </View>

      {/* DJ Visualizer & Speech Subtitles */}
      <DJVisualizer isSpeaking={isDJSpeaking} subtitle={djSubtitle} vibe={currentVibe} />

      {/* Track Details */}
      <View style={styles.detailsContainer}>
        <View style={styles.titleWrapper}>
          <Text style={styles.songTitle} numberOfLines={1}>{songName}</Text>
          <Text style={styles.artistName} numberOfLines={1}>{artistName}</Text>
        </View>

        <TouchableOpacity onPress={toggleDJ} style={[styles.djToggleBtn, isDJEnabled && styles.djToggleActive]}>
          <MaterialCommunityIcons
            name="robot-happy-outline"
            size={22}
            color={isDJEnabled ? '#121212' : '#888888'}
          />
          <Text style={[styles.djToggleText, isDJEnabled && styles.djToggleTextActive]}>
            {isDJEnabled ? 'DJ X ON' : 'DJ X OFF'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Scrubber Bar */}
      <View style={styles.scrubberContainer}>
        <TouchableOpacity
          activeOpacity={1}
          style={styles.scrubberTrack}
          onPress={(e) => {
            const clickX = e.nativeEvent.locationX;
            const barWidth = width - 48;
            const ratio = Math.max(0, Math.min(1, clickX / barWidth));
            const newMillis = ratio * durationMillis;
            seekTo(newMillis);
          }}
        >
          <View style={[styles.scrubberFill, { width: `${Math.min(100, Math.max(0, progress))}%` }]} />
          <View style={[styles.scrubberKnob, { left: `${Math.min(97, Math.max(0, progress))}%` }]} />
        </TouchableOpacity>

        <View style={styles.timeRow}>
          <Text style={styles.timeText}>{formatTime(isSeeking ? seekPos : positionMillis)}</Text>
          <Text style={styles.timeText}>{formatTime(durationMillis)}</Text>
        </View>
      </View>

      {/* Playback Controls */}
      <View style={styles.controlsRow}>
        <TouchableOpacity
          style={styles.secondaryBtn}
          onPress={toggleAutoplay}
        >
          <MaterialCommunityIcons
            name="infinity"
            size={26}
            color={isAutoplayEnabled ? '#1DB954' : '#666666'}
          />
        </TouchableOpacity>

        <TouchableOpacity style={styles.skipBtn} onPress={skipPrevious}>
          <Ionicons name="play-skip-back" size={32} color="#ffffff" />
        </TouchableOpacity>

        {isLoadingTrack ? (
          <View style={styles.playPauseBtn}>
            <ActivityIndicator size="large" color="#121212" />
          </View>
        ) : (
          <TouchableOpacity style={styles.playPauseBtn} onPress={togglePlayPause}>
            <Ionicons
              name={isPlaying ? 'pause' : 'play'}
              size={36}
              color="#121212"
              style={isPlaying ? {} : { marginLeft: 3 }}
            />
          </TouchableOpacity>
        )}

        <TouchableOpacity style={styles.skipBtn} onPress={skipNext}>
          <Ionicons name="play-skip-forward" size={32} color="#ffffff" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.secondaryBtn} onPress={onOpenQueue}>
          <MaterialCommunityIcons name="playlist-play" size={28} color="#b3b3b3" />
        </TouchableOpacity>
      </View>

      {/* Footer Info */}
      <View style={styles.footer}>
        <View style={styles.footerDevice}>
          <MaterialCommunityIcons name="cellphone-sound" size={16} color="#1DB954" />
          <Text style={styles.footerDeviceText}>Streaming on Mobile Phone</Text>
        </View>
        <Text style={styles.footerTechText}>Neural TTS • High-Fidelity Audio</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
    justifyContent: 'space-between',
    paddingBottom: 28,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 10,
  },
  topBarBtn: {
    padding: 6,
  },
  topBarCenter: {
    alignItems: 'center',
  },
  stationLabel: {
    color: '#b3b3b3',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.2,
  },
  stationName: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
    marginTop: 2,
  },
  artworkContainer: {
    alignItems: 'center',
    marginVertical: 12,
  },
  artworkWrapper: {
    width: ARTWORK_SIZE,
    height: ARTWORK_SIZE,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#282828',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.6,
    shadowRadius: 18,
    elevation: 12,
  },
  artworkSpeakingBorder: {
    borderColor: '#1DB954',
    borderWidth: 2.5,
  },
  artwork: {
    width: '100%',
    height: '100%',
  },
  artworkPlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1c1c1c',
  },
  djSpeakingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  djSpeakingText: {
    color: '#1DB954',
    fontWeight: '900',
    fontSize: 15,
    marginTop: 8,
    letterSpacing: 1.5,
  },
  detailsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    marginTop: 6,
  },
  titleWrapper: {
    flex: 1,
    marginRight: 16,
  },
  songTitle: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '800',
    letterSpacing: -0.3,
  },
  artistName: {
    color: '#b3b3b3',
    fontSize: 15,
    fontWeight: '500',
    marginTop: 3,
  },
  djToggleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 18,
    backgroundColor: '#242424',
    borderWidth: 1,
    borderColor: '#383838',
    gap: 6,
  },
  djToggleActive: {
    backgroundColor: '#1DB954',
    borderColor: '#1DB954',
  },
  djToggleText: {
    color: '#888888',
    fontSize: 11,
    fontWeight: '800',
  },
  djToggleTextActive: {
    color: '#121212',
  },
  scrubberContainer: {
    paddingHorizontal: 24,
    marginTop: 14,
  },
  scrubberTrack: {
    height: 4,
    backgroundColor: '#383838',
    borderRadius: 2,
    position: 'relative',
    justifyContent: 'center',
  },
  scrubberFill: {
    height: '100%',
    backgroundColor: '#ffffff',
    borderRadius: 2,
  },
  scrubberKnob: {
    position: 'absolute',
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#ffffff',
    marginLeft: -6,
  },
  timeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  timeText: {
    color: '#b3b3b3',
    fontSize: 11,
    fontWeight: '600',
  },
  controlsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 28,
    marginTop: 10,
  },
  secondaryBtn: {
    padding: 10,
  },
  skipBtn: {
    padding: 10,
  },
  playPauseBtn: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: '#1DB954',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#1DB954',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 10,
    elevation: 8,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 28,
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#1e1e1e',
    paddingTop: 12,
  },
  footerDevice: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  footerDeviceText: {
    color: '#1DB954',
    fontSize: 12,
    fontWeight: '600',
  },
  footerTechText: {
    color: '#666666',
    fontSize: 11,
    fontWeight: '500',
  },
});
