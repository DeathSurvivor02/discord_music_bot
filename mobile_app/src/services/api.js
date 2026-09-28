import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY_SERVER_URL = '@spotify_dj_server_url';
export const DEFAULT_SERVER_URL = 'https://funny-gecko-6.loca.lt';
export const FALLBACK_TUNNEL_URL = 'https://funny-gecko-6.loca.lt';

const getBrowserOrigin = () => {
  if (typeof window !== 'undefined' && window.location && window.location.origin) {
    const o = window.location.origin;
    // Never treat Metro bundler (port 8081 or exp.direct) as the audio API server
    if (o.includes(':8081') || o.includes('exp.direct')) {
      return null;
    }
    if (o.startsWith('http')) return o;
  }
  return null;
};

let cachedServerUrl = null;

export const getServerUrl = async () => {
  if (cachedServerUrl) return cachedServerUrl;
  const origin = getBrowserOrigin();
  if (origin) {
    cachedServerUrl = origin;
    return cachedServerUrl;
  }
  try {
    const saved = await AsyncStorage.getItem(STORAGE_KEY_SERVER_URL);
    // If saved URL contains 8081 or is outdated LAN HTTP, reset to HTTPS tunnel
    if (!saved || saved.includes(':8081') || saved.includes('exp.direct') || saved.includes('10.0.0.138') || saved.includes('silly-socks')) {
      cachedServerUrl = DEFAULT_SERVER_URL;
      await AsyncStorage.setItem(STORAGE_KEY_SERVER_URL, DEFAULT_SERVER_URL);
    } else {
      cachedServerUrl = saved;
    }
  } catch {
    cachedServerUrl = DEFAULT_SERVER_URL;
  }
  return cachedServerUrl;
};



export const setServerUrl = async (url) => {
  const cleanUrl = url.trim().replace(/\/+$/, '');
  cachedServerUrl = cleanUrl;
  await AsyncStorage.setItem(STORAGE_KEY_SERVER_URL, cleanUrl);
  return cleanUrl;
};

export const getFullAudioUrl = async (path) => {
  if (!path) return null;
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  const base = await getServerUrl();
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${cleanPath}`;
};

const fetchJson = async (endpoint, options = {}) => {
  let base = await getServerUrl();
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeout || 30000);

  const doRequest = async (baseUrl) => {
    const response = await fetch(`${baseUrl}${endpoint}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        'Bypass-Tunnel-Reminder': 'true',
        ...(options.headers || {}),
      },
    });
    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`API Error ${response.status}: ${errText || response.statusText}`);
    }
    return await response.json();
  };

  try {
    const res = await doRequest(base);
    clearTimeout(timeoutId);
    return res;
  } catch (err) {
    // If LAN fails and we haven't tried the tunnel, try fallback tunnel
    if (base !== FALLBACK_TUNNEL_URL) {
      try {
        const fallbackRes = await doRequest(FALLBACK_TUNNEL_URL);
        clearTimeout(timeoutId);
        await setServerUrl(FALLBACK_TUNNEL_URL);
        return fallbackRes;
      } catch {}
    }
    clearTimeout(timeoutId);
    throw err;
  }
};


export const checkHealth = async () => {
  return await fetchJson('/api/health', { timeout: 6000 });
};

export const searchTracks = async (query) => {
  const encoded = encodeURIComponent(query);
  return await fetchJson(`/api/search?q=${encoded}`);
};

export const resolveStream = async (searchQuery, title = null) => {
  return await fetchJson('/api/resolve', {
    method: 'POST',
    body: JSON.stringify({
      search_query: searchQuery,
      title: title,
    }),
    timeout: 35000,
  });
};

export const startVibeSession = async (vibe, voice = null) => {
  return await fetchJson('/api/dj/session', {
    method: 'POST',
    body: JSON.stringify({
      vibe: vibe,
      voice: voice,
    }),
    timeout: 45000,
  });
};

export const generateDJIntro = async ({ nextTrack, prevTrack = null, vibe = null, voice = null, isFirst = false }) => {
  return await fetchJson('/api/dj/intro', {
    method: 'POST',
    body: JSON.stringify({
      next_track: nextTrack,
      prev_track: prevTrack,
      vibe: vibe,
      voice: voice,
      is_first: isFirst,
    }),
    timeout: 25000,
  });
};

export const getAutoplayTracks = async (lastTrack, history = [], limit = 5) => {
  return await fetchJson('/api/autoplay', {
    method: 'POST',
    body: JSON.stringify({
      last_track: lastTrack,
      history: history,
      limit: limit,
    }),
    timeout: 25000,
  });
};
