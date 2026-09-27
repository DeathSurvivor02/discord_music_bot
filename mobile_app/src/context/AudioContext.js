import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { createAudioPlayer, setAudioModeAsync } from 'expo-audio';
import * as api from '../services/api';

const AudioContext = createContext(null);

export const AudioProvider = ({ children }) => {
  const [currentTrack, setCurrentTrack] = useState(null);
  const [queue, setQueue] = useState([]);
  const [history, setHistory] = useState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoadingTrack, setIsLoadingTrack] = useState(false);
  const [isDJSpeaking, setIsDJSpeaking] = useState(false);
  const [djSubtitle, setDjSubtitle] = useState('');
  const [positionSec, setPositionSec] = useState(0);
  const [durationSec, setDurationSec] = useState(0);
  const [isAutoplayEnabled, setIsAutoplayEnabled] = useState(true);
  const [isDJEnabled, setIsDJEnabled] = useState(true);
  const [currentVibe, setCurrentVibe] = useState("Today's Top Hits");
  const [serverOnline, setServerOnline] = useState(false);
  const [serverUrl, setServerUrlState] = useState(api.DEFAULT_SERVER_URL);
  const [errorMsg, setErrorMsg] = useState(null);

  const musicPlayerRef = useRef(null);
  const djPlayerRef = useRef(null);
  const musicListenerRef = useRef(null);
  const songsSinceLastDJRef = useRef(0);

  // Initialize Audio Mode for mobile
  useEffect(() => {
    const initAudio = async () => {
      try {
        await setAudioModeAsync({
          playsInSilentMode: true,
          shouldPlayInBackground: true,
        });
      } catch (e) {
        console.warn('Audio mode error:', e);
      }
    };
    initAudio();

    // Check server status
    checkConnection();
    const interval = setInterval(checkConnection, 15000);
    return () => clearInterval(interval);
  }, []);

  const checkConnection = async () => {
    try {
      const url = await api.getServerUrl();
      setServerUrlState(url);
      const res = await api.checkHealth();
      setServerOnline(res && res.status === 'online');
    } catch {
      setServerOnline(false);
    }
  };

  const updateServerUrl = async (newUrl) => {
    const saved = await api.setServerUrl(newUrl);
    setServerUrlState(saved);
    await checkConnection();
  };

  // Cleanup all players
  const stopAllSounds = () => {
    if (musicListenerRef.current) {
      try { musicListenerRef.current.remove(); } catch {}
      musicListenerRef.current = null;
    }
    if (djPlayerRef.current) {
      try {
        djPlayerRef.current.pause();
        djPlayerRef.current.remove();
      } catch {}
      djPlayerRef.current = null;
    }
    if (musicPlayerRef.current) {
      try {
        musicPlayerRef.current.pause();
        musicPlayerRef.current.remove();
      } catch {}
      musicPlayerRef.current = null;
    }
    setIsDJSpeaking(false);
    setIsPlaying(false);
  };

  // Play a DJ audio clip before music starts
  const playDJClip = async (audioUrl, subtitleText) => {
    if (!audioUrl || !isDJEnabled) return;
    try {
      setIsDJSpeaking(true);
      setDjSubtitle(subtitleText || 'DJ X on the air...');
      const fullUrl = await api.getFullAudioUrl(audioUrl);

      const djPlayer = createAudioPlayer({ uri: fullUrl }, { updateInterval: 250 });
      djPlayerRef.current = djPlayer;

      await new Promise((resolve) => {
        let finished = false;
        const sub = djPlayer.addListener('playbackStatusUpdate', (status) => {
          if (status.didJustFinish && !finished) {
            finished = true;
            try { sub.remove(); } catch {}
            resolve();
          }
        });
        djPlayer.play();

        // Safety timeout in case audio finishes without event
        setTimeout(() => {
          if (!finished) {
            finished = true;
            try { sub.remove(); } catch {}
            resolve();
          }
        }, 12000);
      });

      try {
        djPlayer.pause();
        djPlayer.remove();
      } catch {}
      djPlayerRef.current = null;
    } catch (e) {
      console.warn('DJ audio error:', e);
    } finally {
      setIsDJSpeaking(false);
    }
  };

  // Main playback engine for a track
  const executePlayTrack = async (track, djIntroObj = null) => {
    setIsLoadingTrack(true);
    setErrorMsg(null);
    stopAllSounds();
    setCurrentTrack(track);

    // 1. Play DJ intro if available
    if (djIntroObj && djIntroObj.audio_url && isDJEnabled) {
      await playDJClip(djIntroObj.audio_url, djIntroObj.text);
    }

    // 2. Resolve music stream URL if not already present
    let streamUrl = track.stream_url;
    let thumb = track.thumbnail;
    let duration = track.duration || 0;

    try {
      if (!streamUrl) {
        const query = track.search_query || track.title;
        const resolved = await api.resolveStream(query, track.title);
        streamUrl = resolved.stream_url;
        thumb = resolved.thumbnail || thumb;
        duration = resolved.duration || duration;
        track.stream_url = streamUrl;
        track.thumbnail = thumb;
        track.duration = duration;
        setCurrentTrack({ ...track });
      }

      if (!streamUrl) {
        throw new Error('No stream URL available');
      }

      // 3. Play the music stream using native expo-audio
      const player = createAudioPlayer({ uri: streamUrl }, { updateInterval: 500 });
      musicPlayerRef.current = player;

      const sub = player.addListener('playbackStatusUpdate', (status) => {
        setIsPlaying(status.playing);
        if (status.currentTime !== undefined) {
          setPositionSec(status.currentTime);
        }
        if (status.duration > 0) {
          setDurationSec(status.duration);
        }
        if (status.didJustFinish) {
          handleTrackEnd();
        }
      });
      musicListenerRef.current = sub;

      player.play();
      setIsPlaying(true);
      setIsLoadingTrack(false);
      setPositionSec(0);
      setDurationSec(duration);
      songsSinceLastDJRef.current += 1;
    } catch (err) {
      console.error('Track playback error:', err);
      setIsLoadingTrack(false);
      setErrorMsg(`Failed to play ${track.title}. Skipping...`);
      setTimeout(() => skipNext(), 2000);
    }
  };

  // Track ended automatically
  const handleTrackEnd = async () => {
    if (currentTrack) {
      setHistory((prev) => [...prev, currentTrack.title]);
    }
    await advanceNextTrack();
  };

  // Advance to next song or trigger autoplay
  const advanceNextTrack = async () => {
    if (queue.length > 0) {
      const next = queue[0];
      const newQueue = queue.slice(1);
      setQueue(newQueue);

      // Check if DJ X should speak (every 2-3 tracks)
      let djIntro = null;
      if (isDJEnabled && (songsSinceLastDJRef.current >= 2 || songsSinceLastDJRef.current === 0)) {
        try {
          const introData = await api.generateDJIntro({
            nextTrack: next.title,
            prevTrack: currentTrack ? currentTrack.title : null,
            vibe: currentVibe,
          });
          djIntro = {
            audio_url: introData.audio_url,
            text: introData.speech_text,
          };
          songsSinceLastDJRef.current = 0;
        } catch (e) {
          console.warn('DJ intro error:', e);
        }
      }

      await executePlayTrack(next, djIntro);
    } else if (isAutoplayEnabled && currentTrack) {
      // Endless Autoplay with YouTube Music Radio!
      setIsLoadingTrack(true);
      setDjSubtitle('DJ X finding next tracks for you...');
      try {
        const hist = [...history, currentTrack.title];
        const res = await api.getAutoplayTracks(currentTrack.title, hist, 5);
        const recTracks = res.tracks || [];

        if (recTracks.length > 0) {
          const firstRec = recTracks[0];
          const remainingRecs = recTracks.slice(1);
          setQueue(remainingRecs);

          let djIntro = null;
          if (isDJEnabled) {
            try {
              const introData = await api.generateDJIntro({
                nextTrack: firstRec.title,
                prevTrack: currentTrack.title,
                vibe: currentVibe,
              });
              djIntro = {
                audio_url: introData.audio_url,
                text: introData.speech_text,
              };
              songsSinceLastDJRef.current = 0;
            } catch {}
          }

          await executePlayTrack(firstRec, djIntro);
        } else {
          setIsLoadingTrack(false);
        }
      } catch (err) {
        console.error('Autoplay error:', err);
        setIsLoadingTrack(false);
      }
    } else {
      setIsPlaying(false);
      setCurrentTrack(null);
    }
  };

  // Launch a 1-tap vibe mix
  const playVibeSession = async (vibeName) => {
    setIsLoadingTrack(true);
    setCurrentVibe(vibeName);
    setErrorMsg(null);
    try {
      const data = await api.startVibeSession(vibeName);
      if (!data.tracks || data.tracks.length === 0) {
        throw new Error('No tracks found for this vibe');
      }

      const firstTrack = data.tracks[0];
      const remainingTracks = data.tracks.slice(1);
      setQueue(remainingTracks);

      const djIntro = data.dj_intro ? {
        audio_url: data.dj_intro.audio_url,
        text: data.dj_intro.text,
      } : null;

      songsSinceLastDJRef.current = 0;
      await executePlayTrack(firstTrack, djIntro);
    } catch (err) {
      console.error('Start vibe error:', err);
      setErrorMsg(`Could not start ${vibeName}: ${err.message}`);
      setIsLoadingTrack(false);
    }
  };

  // Controls
  const togglePlayPause = () => {
    if (!musicPlayerRef.current) return;
    try {
      if (isPlaying) {
        musicPlayerRef.current.pause();
        setIsPlaying(false);
      } else {
        musicPlayerRef.current.play();
        setIsPlaying(true);
      }
    } catch (e) {
      console.warn('togglePlayPause error:', e);
    }
  };

  const seekTo = (millis) => {
    if (!musicPlayerRef.current) return;
    try {
      const sec = millis / 1000;
      musicPlayerRef.current.seekTo(sec);
      setPositionSec(sec);
    } catch (e) {
      console.warn('seekTo error:', e);
    }
  };

  const skipNext = async () => {
    if (currentTrack) {
      setHistory((prev) => [...prev, currentTrack.title]);
    }
    await advanceNextTrack();
  };

  const skipPrevious = async () => {
    if (positionSec > 5) {
      seekTo(0);
      return;
    }
    if (history.length > 0) {
      const prevTitle = history[history.length - 1];
      setHistory((prev) => prev.slice(0, -1));
      if (currentTrack) {
        setQueue((prev) => [currentTrack, ...prev]);
      }
      await executePlayTrack({ title: prevTitle, search_query: prevTitle });
    } else {
      seekTo(0);
    }
  };

  const addToQueue = (track) => {
    setQueue((prev) => [...prev, track]);
  };

  const removeFromQueue = (index) => {
    setQueue((prev) => prev.filter((_, i) => i !== index));
  };

  const playNow = async (track) => {
    if (currentTrack) {
      setHistory((prev) => [...prev, currentTrack.title]);
    }
    await executePlayTrack(track);
  };

  return (
    <AudioContext.Provider
      value={{
        currentTrack,
        queue,
        history,
        isPlaying,
        isLoadingTrack,
        isDJSpeaking,
        djSubtitle,
        positionMillis: positionSec * 1000,
        durationMillis: durationSec * 1000,
        isAutoplayEnabled,
        isDJEnabled,
        currentVibe,
        serverOnline,
        serverUrl,
        errorMsg,
        playVibeSession,
        playNow,
        togglePlayPause,
        seekTo,
        skipNext,
        skipPrevious,
        addToQueue,
        removeFromQueue,
        toggleAutoplay: () => setIsAutoplayEnabled((v) => !v),
        toggleDJ: () => setIsDJEnabled((v) => !v),
        refreshServerStatus: checkConnection,
        updateServerUrl,
      }}
    >
      {children}
    </AudioContext.Provider>
  );
};

export const useAudio = () => useContext(AudioContext);
