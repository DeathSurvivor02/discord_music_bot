import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';

export const DJVisualizer = ({ isSpeaking, subtitle, vibe }) => {
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const bar1 = useRef(new Animated.Value(10)).current;
  const bar2 = useRef(new Animated.Value(20)).current;
  const bar3 = useRef(new Animated.Value(15)).current;
  const bar4 = useRef(new Animated.Value(25)).current;

  useEffect(() => {
    if (isSpeaking) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.15,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();

      const animateBar = (anim, min, max, dur) => {
        return Animated.loop(
          Animated.sequence([
            Animated.timing(anim, {
              toValue: max,
              duration: dur,
              useNativeDriver: false,
            }),
            Animated.timing(anim, {
              toValue: min,
              duration: dur,
              useNativeDriver: false,
            }),
          ])
        );
      };

      const b1 = animateBar(bar1, 6, 28, 280);
      const b2 = animateBar(bar2, 10, 36, 340);
      const b3 = animateBar(bar3, 8, 30, 260);
      const b4 = animateBar(bar4, 12, 38, 310);

      b1.start();
      b2.start();
      b3.start();
      b4.start();

      return () => {
        pulse.stop();
        b1.stop();
        b2.stop();
        b3.stop();
        b4.stop();
      };
    } else {
      pulseAnim.setValue(1);
      bar1.setValue(6);
      bar2.setValue(10);
      bar3.setValue(8);
      bar4.setValue(12);
    }
  }, [isSpeaking]);

  if (!isSpeaking) return null;

  return (
    <View style={styles.container}>
      <Animated.View style={[styles.djBadge, { transform: [{ scale: pulseAnim }] }]}>
        <MaterialCommunityIcons name="radio-tower" size={24} color="#1DB954" />
        <Text style={styles.djBadgeText}>DJ X ON THE AIR</Text>
        <View style={styles.barsContainer}>
          <Animated.View style={[styles.waveBar, { height: bar1 }]} />
          <Animated.View style={[styles.waveBar, { height: bar2 }]} />
          <Animated.View style={[styles.waveBar, { height: bar3 }]} />
          <Animated.View style={[styles.waveBar, { height: bar4 }]} />
        </View>
      </Animated.View>

      {subtitle ? (
        <View style={styles.subtitleBox}>
          <Text style={styles.subtitleText} numberOfLines={3}>
            "{subtitle}"
          </Text>
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 12,
    alignItems: 'center',
    width: '100%',
    paddingHorizontal: 20,
  },
  djBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0c2714',
    borderColor: '#1DB954',
    borderWidth: 1.5,
    borderRadius: 24,
    paddingVertical: 8,
    paddingHorizontal: 16,
    shadowColor: '#1DB954',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 10,
    elevation: 8,
  },
  djBadgeText: {
    color: '#1DB954',
    fontWeight: '800',
    fontSize: 13,
    letterSpacing: 1.2,
    marginLeft: 8,
    marginRight: 12,
  },
  barsContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    height: 24,
    gap: 3,
  },
  waveBar: {
    width: 3.5,
    backgroundColor: '#1DB954',
    borderRadius: 2,
  },
  subtitleBox: {
    marginTop: 10,
    backgroundColor: 'rgba(25, 25, 25, 0.9)',
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderLeftWidth: 3,
    borderLeftColor: '#1DB954',
    width: '100%',
  },
  subtitleText: {
    color: '#e0e0e0',
    fontSize: 14,
    fontStyle: 'italic',
    lineHeight: 20,
    textAlign: 'center',
  },
});
