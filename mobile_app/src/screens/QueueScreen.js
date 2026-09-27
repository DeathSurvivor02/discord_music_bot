import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Image,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { useAudio } from '../context/AudioContext';

export const QueueScreen = ({ onClose }) => {
  const {
    currentTrack,
    queue,
    playNow,
    removeFromQueue,
    isDJSpeaking,
    isAutoplayEnabled,
    currentVibe,
  } = useAudio();

  const formatSec = (sec) => {
    if (!sec || isNaN(sec)) return '';
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
          <Ionicons name="arrow-back" size={26} color="#ffffff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Queue</Text>
        <View style={{ width: 26 }} />
      </View>

      <ScrollView style={styles.scrollArea} contentContainerStyle={styles.scrollContent}>
        {/* Now Playing Section */}
        <Text style={styles.sectionHeader}>NOW PLAYING</Text>
        {currentTrack ? (
          <View style={styles.nowPlayingCard}>
            {currentTrack.thumbnail ? (
              <Image source={{ uri: currentTrack.thumbnail }} style={styles.thumb} />
            ) : (
              <View style={[styles.thumb, styles.thumbPlaceholder]}>
                <MaterialCommunityIcons name="music" size={24} color="#1DB954" />
              </View>
            )}

            <View style={styles.trackInfo}>
              <Text style={styles.trackTitle} numberOfLines={1}>{currentTrack.title}</Text>
              <Text style={styles.trackSubtitle}>
                {isDJSpeaking ? '🎙️ DJ X Speaking Live' : `Vibe: ${currentVibe}`}
              </Text>
            </View>

            <MaterialCommunityIcons name="volume-high" size={24} color="#1DB954" />
          </View>
        ) : (
          <Text style={styles.emptyText}>Nothing currently playing.</Text>
        )}

        {/* Upcoming Queue */}
        <View style={styles.queueHeaderRow}>
          <Text style={styles.sectionHeader}>NEXT UP ({queue.length})</Text>
        </View>

        {queue.length === 0 ? (
          <View style={styles.emptyQueueBox}>
            <MaterialCommunityIcons name="playlist-remove" size={40} color="#555" />
            <Text style={styles.emptyQueueTitle}>No tracks manually queued</Text>
            <Text style={styles.emptyQueueSubtitle}>
              {isAutoplayEnabled
                ? "Don't worry! Autoplay is ON. DJ X will automatically introduce fresh matching songs when the current song ends."
                : "Autoplay is OFF. Playback will stop when the current song finishes."}
            </Text>
          </View>
        ) : (
          queue.map((track, index) => {
            const hasDJDrop = index % 3 === 1; // DJ drop indicator every few tracks
            return (
              <View key={index} style={styles.queueItem}>
                <TouchableOpacity
                  style={styles.queueItemMain}
                  onPress={() => {
                    removeFromQueue(index);
                    playNow(track);
                  }}
                >
                  <Text style={styles.queueIndex}>{index + 1}</Text>
                  {track.thumbnail ? (
                    <Image source={{ uri: track.thumbnail }} style={styles.queueThumb} />
                  ) : (
                    <View style={[styles.queueThumb, styles.thumbPlaceholder]}>
                      <MaterialCommunityIcons name="music-note" size={16} color="#888" />
                    </View>
                  )}

                  <View style={styles.queueInfo}>
                    <Text style={styles.queueTitle} numberOfLines={1}>{track.title}</Text>
                    <View style={styles.queueMetaRow}>
                      {hasDJDrop && (
                        <View style={styles.djDropTag}>
                          <MaterialCommunityIcons name="microphone" size={10} color="#1DB954" />
                          <Text style={styles.djDropTagText}>DJ X Drop</Text>
                        </View>
                      )}
                      {track.duration > 0 && (
                        <Text style={styles.queueDuration}>{formatSec(track.duration)}</Text>
                      )}
                    </View>
                  </View>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.removeBtn}
                  onPress={() => removeFromQueue(index)}
                >
                  <Ionicons name="trash-outline" size={20} color="#777" />
                </TouchableOpacity>
              </View>
            );
          })
        )}

        {/* Endless Autoplay Banner */}
        {isAutoplayEnabled && (
          <View style={styles.autoplayBanner}>
            <View style={styles.autoplayIcon}>
              <MaterialCommunityIcons name="infinity" size={28} color="#1DB954" />
            </View>
            <View style={styles.autoplayTextWrapper}>
              <Text style={styles.autoplayTitle}>Endless Autoplay Active</Text>
              <Text style={styles.autoplayDesc}>
                Using YouTube Music Radio's intelligence to queue up similar hits across diverse artists.
              </Text>
            </View>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 52,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#202020',
  },
  closeBtn: {
    padding: 4,
  },
  headerTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '800',
  },
  scrollArea: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 60,
  },
  sectionHeader: {
    color: '#888888',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 1,
    marginBottom: 10,
  },
  nowPlayingCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1c1c1c',
    borderRadius: 12,
    padding: 12,
    marginBottom: 24,
    borderLeftWidth: 3,
    borderLeftColor: '#1DB954',
  },
  thumb: {
    width: 48,
    height: 48,
    borderRadius: 8,
    backgroundColor: '#282828',
  },
  thumbPlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  trackInfo: {
    flex: 1,
    marginHorizontal: 12,
  },
  trackTitle: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },
  trackSubtitle: {
    color: '#1DB954',
    fontSize: 12,
    marginTop: 2,
    fontWeight: '600',
  },
  emptyText: {
    color: '#666',
    fontSize: 14,
    marginBottom: 20,
  },
  queueHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  emptyQueueBox: {
    alignItems: 'center',
    paddingVertical: 36,
    paddingHorizontal: 20,
    backgroundColor: '#181818',
    borderRadius: 12,
    marginBottom: 20,
  },
  emptyQueueTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
    marginTop: 10,
  },
  emptyQueueSubtitle: {
    color: '#888888',
    fontSize: 13,
    textAlign: 'center',
    marginTop: 6,
    lineHeight: 18,
  },
  queueItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#222222',
  },
  queueItemMain: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  queueIndex: {
    color: '#666666',
    fontSize: 13,
    fontWeight: '700',
    width: 24,
  },
  queueThumb: {
    width: 40,
    height: 40,
    borderRadius: 6,
    backgroundColor: '#282828',
  },
  queueInfo: {
    flex: 1,
    marginHorizontal: 10,
  },
  queueTitle: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  queueMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 3,
    gap: 8,
  },
  djDropTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0c2b16',
    paddingVertical: 1,
    paddingHorizontal: 6,
    borderRadius: 10,
    gap: 3,
  },
  djDropTagText: {
    color: '#1DB954',
    fontSize: 10,
    fontWeight: '700',
  },
  queueDuration: {
    color: '#777',
    fontSize: 11,
  },
  removeBtn: {
    padding: 8,
  },
  autoplayBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#18241c',
    borderRadius: 12,
    padding: 14,
    marginTop: 20,
    borderWidth: 1,
    borderColor: '#194928',
  },
  autoplayIcon: {
    marginRight: 12,
  },
  autoplayTextWrapper: {
    flex: 1,
  },
  autoplayTitle: {
    color: '#1DB954',
    fontSize: 14,
    fontWeight: '800',
  },
  autoplayDesc: {
    color: '#9cc7a9',
    fontSize: 12,
    marginTop: 2,
    lineHeight: 16,
  },
});
