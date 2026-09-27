import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Modal,
  Alert,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons, FontAwesome5 } from '@expo/vector-icons';
import { useAudio } from '../context/AudioContext';
import * as api from '../services/api';

const VIBE_CARDS = [
  { id: '1', title: "Today's Top Hits", color: '#E13300', icon: 'fire', desc: 'Hottest global chart toppers' },
  { id: '2', title: 'Rap & Hip Hop', color: '#B02897', icon: 'microphone-alt', desc: 'Heavy 808s, bars, and trap' },
  { id: '3', title: 'Chill & Lo-Fi', color: '#477D95', icon: 'coffee', desc: 'Laid back study and relax vibes' },
  { id: '4', title: 'Workout Energy', color: '#1E3264', icon: 'bolt', desc: 'High BPM pump up anthems' },
  { id: '5', title: 'Classic & Alt Rock', color: '#E91429', icon: 'guitar', desc: 'Iconic guitar riffs and grunge' },
  { id: '6', title: 'Late Night Drive', color: '#503750', icon: 'car', desc: 'Synthwave, melodic R&B, neon mood' },
  { id: '7', title: 'Party & Club Bangers', color: '#AF2896', icon: 'compact-disc', desc: 'EDM, dance, house bangers' },
  { id: '8', title: 'Indie & Alternative', color: '#0D73EC', icon: 'headphones', desc: 'Fresh bedroom pop & indie gems' },
];

export const HomeScreen = ({ onOpenPlayer }) => {
  const {
    playVibeSession,
    playNow,
    isLoadingTrack,
    currentVibe,
    serverOnline,
    serverUrl,
    updateServerUrl,
    refreshServerStatus,
  } = useAudio();

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [tempServerUrl, setTempServerUrl] = useState(serverUrl);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const res = await api.searchTracks(searchQuery);
      setSearchResults(res.tracks || []);
    } catch (e) {
      Alert.alert('Search Failed', e.message || 'Could not find tracks.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectTrack = async (track) => {
    setSearchResults([]);
    setSearchQuery('');
    await playNow(track);
    if (onOpenPlayer) onOpenPlayer();
  };

  const handleSelectVibe = async (vibeTitle) => {
    await playVibeSession(vibeTitle);
    if (onOpenPlayer) onOpenPlayer();
  };

  const handleSaveServerUrl = async () => {
    if (!tempServerUrl.trim()) return;
    await updateServerUrl(tempServerUrl);
    setShowSettingsModal(false);
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Spotify AI DJ</Text>
          <Text style={styles.subGreeting}>Your personal radio station with DJ X</Text>
        </View>

        <TouchableOpacity
          style={[styles.statusBadge, { backgroundColor: serverOnline ? '#0f381c' : '#381414' }]}
          onPress={() => {
            setTempServerUrl(serverUrl);
            setShowSettingsModal(true);
          }}
        >
          <View style={[styles.statusDot, { backgroundColor: serverOnline ? '#1DB954' : '#E91429' }]} />
          <Text style={[styles.statusText, { color: serverOnline ? '#1DB954' : '#E91429' }]}>
            {serverOnline ? 'Connected' : 'Offline'}
          </Text>
          <Ionicons name="settings-sharp" size={14} color="#888" style={{ marginLeft: 6 }} />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollArea} contentContainerStyle={styles.scrollContent}>
        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <Ionicons name="search" size={20} color="#b3b3b3" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search any song, artist, or album..."
            placeholderTextColor="#777"
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={handleSearch}
            returnKeyType="search"
          />
          {searchQuery ? (
            <TouchableOpacity onPress={() => setSearchQuery('')} style={styles.clearBtn}>
              <Ionicons name="close-circle" size={18} color="#888" />
            </TouchableOpacity>
          ) : null}
          {isSearching ? (
            <ActivityIndicator size="small" color="#1DB954" style={{ marginRight: 8 }} />
          ) : (
            <TouchableOpacity onPress={handleSearch} style={styles.searchActionBtn}>
              <Text style={styles.searchActionText}>Go</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Search Results */}
        {searchResults.length > 0 ? (
          <View style={styles.resultsContainer}>
            <View style={styles.resultsHeader}>
              <Text style={styles.sectionTitle}>Search Results</Text>
              <TouchableOpacity onPress={() => setSearchResults([])}>
                <Text style={styles.dismissText}>Clear</Text>
              </TouchableOpacity>
            </View>
            {searchResults.map((item, idx) => (
              <TouchableOpacity
                key={idx}
                style={styles.resultItem}
                onPress={() => handleSelectTrack(item)}
              >
                <MaterialCommunityIcons name="music-circle-outline" size={28} color="#1DB954" />
                <View style={styles.resultInfo}>
                  <Text style={styles.resultTitle} numberOfLines={1}>{item.title}</Text>
                  <Text style={styles.resultSubtitle}>Play now with DJ commentary</Text>
                </View>
                <Ionicons name="play-circle" size={28} color="#1DB954" />
              </TouchableOpacity>
            ))}
          </View>
        ) : null}

        {/* DJ Banner */}
        <View style={styles.djHeroBanner}>
          <View style={styles.djHeroIconBox}>
            <MaterialCommunityIcons name="waveform" size={32} color="#121212" />
          </View>
          <View style={styles.djHeroText}>
            <Text style={styles.djHeroTitle}>DJ X IS READY</Text>
            <Text style={styles.djHeroDesc}>
              Tap any vibe below. DJ X will drop a live intro, spin matching tracks, and keep the music flowing forever.
            </Text>
          </View>
        </View>

        {/* Vibe Mixes Grid */}
        <Text style={styles.sectionTitle}>Pick Your Vibe</Text>
        <View style={styles.grid}>
          {VIBE_CARDS.map((card) => {
            const isCurrent = currentVibe === card.title;
            return (
              <TouchableOpacity
                key={card.id}
                style={[styles.vibeCard, { backgroundColor: card.color }]}
                activeOpacity={0.8}
                onPress={() => handleSelectVibe(card.title)}
                disabled={isLoadingTrack}
              >
                <View style={styles.cardHeader}>
                  <Text style={styles.vibeTitle}>{card.title}</Text>
                  <FontAwesome5 name={card.icon} size={22} color="rgba(255, 255, 255, 0.85)" />
                </View>
                <Text style={styles.vibeDesc}>{card.desc}</Text>

                <View style={styles.cardFooter}>
                  <View style={styles.playPill}>
                    <Ionicons name="play" size={14} color="#121212" />
                    <Text style={styles.playPillText}>Play Mix</Text>
                  </View>
                  {isCurrent && (
                    <Text style={styles.activeVibeBadge}>Active</Text>
                  )}
                </View>
              </TouchableOpacity>
            );
          })}
        </View>
      </ScrollView>

      {/* Settings / IP Configuration Modal */}
      <Modal
        visible={showSettingsModal}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowSettingsModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Backend Server Settings</Text>
              <TouchableOpacity onPress={() => setShowSettingsModal(false)}>
                <Ionicons name="close" size={24} color="#ffffff" />
              </TouchableOpacity>
            </View>

            <Text style={styles.modalLabel}>Local Server URL (Wi-Fi or LAN):</Text>
            <TextInput
              style={styles.modalInput}
              value={tempServerUrl}
              onChangeText={setTempServerUrl}
              placeholder="http://10.0.0.138:8000"
              placeholderTextColor="#666"
              autoCapitalize="none"
              autoCorrect={false}
            />

            <Text style={styles.modalHint}>
              Make sure your phone and your PC are on the same Wi-Fi network. Your PC's detected IP is{' '}
              <Text style={{ color: '#1DB954', fontWeight: 'bold' }}>10.0.0.138:8000</Text>.
            </Text>

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.modalSecondaryBtn}
                onPress={async () => {
                  await refreshServerStatus();
                  Alert.alert('Status Refreshed', serverOnline ? 'Server is ONLINE!' : 'Server unreachable.');
                }}
              >
                <Text style={styles.modalSecondaryText}>Test Link</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.modalPrimaryBtn} onPress={handleSaveServerUrl}>
                <Text style={styles.modalPrimaryText}>Save & Connect</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
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
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 54,
    paddingBottom: 16,
    backgroundColor: '#121212',
  },
  greeting: {
    color: '#ffffff',
    fontSize: 26,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  subGreeting: {
    color: '#a0a0a0',
    fontSize: 13,
    marginTop: 2,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '700',
  },
  scrollArea: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 100,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#242424',
    borderRadius: 10,
    paddingHorizontal: 12,
    height: 48,
    marginTop: 10,
    marginBottom: 16,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    color: '#ffffff',
    fontSize: 15,
  },
  clearBtn: {
    padding: 4,
  },
  searchActionBtn: {
    backgroundColor: '#1DB954',
    borderRadius: 6,
    paddingVertical: 5,
    paddingHorizontal: 12,
  },
  searchActionText: {
    color: '#121212',
    fontWeight: '700',
    fontSize: 13,
  },
  resultsContainer: {
    backgroundColor: '#1c1c1c',
    borderRadius: 12,
    padding: 14,
    marginBottom: 20,
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  dismissText: {
    color: '#1DB954',
    fontSize: 13,
    fontWeight: '600',
  },
  resultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#282828',
  },
  resultInfo: {
    flex: 1,
    marginHorizontal: 12,
  },
  resultTitle: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  resultSubtitle: {
    color: '#888',
    fontSize: 12,
    marginTop: 2,
  },
  djHeroBanner: {
    flexDirection: 'row',
    backgroundColor: '#1DB954',
    borderRadius: 14,
    padding: 16,
    marginBottom: 24,
    alignItems: 'center',
  },
  djHeroIconBox: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#ffffff',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  djHeroText: {
    flex: 1,
  },
  djHeroTitle: {
    color: '#121212',
    fontSize: 16,
    fontWeight: '900',
    letterSpacing: 0.5,
  },
  djHeroDesc: {
    color: '#121212',
    fontSize: 12,
    fontWeight: '500',
    marginTop: 3,
    lineHeight: 16,
  },
  sectionTitle: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '800',
    marginBottom: 14,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  vibeCard: {
    width: '48%',
    height: 140,
    borderRadius: 12,
    padding: 14,
    marginBottom: 14,
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 4,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  vibeTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '800',
    flex: 1,
    marginRight: 6,
  },
  vibeDesc: {
    color: 'rgba(255, 255, 255, 0.85)',
    fontSize: 11,
    marginTop: 4,
    lineHeight: 14,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  playPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 14,
    paddingVertical: 4,
    paddingHorizontal: 10,
    gap: 4,
  },
  playPillText: {
    color: '#121212',
    fontSize: 11,
    fontWeight: '800',
  },
  activeVibeBadge: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'center',
    padding: 24,
  },
  modalContent: {
    backgroundColor: '#242424',
    borderRadius: 16,
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '800',
  },
  modalLabel: {
    color: '#b3b3b3',
    fontSize: 13,
    marginBottom: 8,
  },
  modalInput: {
    backgroundColor: '#181818',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#ffffff',
    fontSize: 15,
    borderWidth: 1,
    borderColor: '#383838',
  },
  modalHint: {
    color: '#888',
    fontSize: 12,
    marginTop: 10,
    lineHeight: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
    marginTop: 20,
  },
  modalSecondaryBtn: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#333',
  },
  modalSecondaryText: {
    color: '#fff',
    fontWeight: '600',
  },
  modalPrimaryBtn: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#1DB954',
  },
  modalPrimaryText: {
    color: '#121212',
    fontWeight: '800',
  },
});
