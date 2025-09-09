import random
import numpy as np
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx, TextClip, CompositeVideoClip

class VideoProcessor:
    def __init__(self):
        self.clips_cache = []

    def process_clips(self, video_paths, audio_analysis, style_preset, velocity_mode, transition_intensity):
        """Cut and process video clips based on audio beats and style"""
        processed_clips = []
        beats = audio_analysis.get('beats', [])
        duration = audio_analysis.get('duration', 30)

        # fallback: evenly spaced beats
        if len(beats) < 2:
            beats = np.linspace(0, duration, 10)

        for i, path in enumerate(video_paths):
            try:
                clip = VideoFileClip(path)
                clip_duration = clip.duration

                # Cut clip into segments based on beats
                segments = []
                for j in range(len(beats)-1):
                    start = min(beats[j], clip_duration)
                    end = min(beats[j+1], clip_duration)
                    if end - start <= 0.1:  # skip too short
                        continue
                    segment = clip.subclip(start, end)

                    # Random reverse
                    if random.random() < 0.15:
                        segment = segment.fx(vfx.time_mirror)

                    # Speed adjustment
                    speed_factor = self._calculate_speed_factor(velocity_mode, audio_analysis, j)
                    segment = segment.fx(vfx.speedx, speed_factor)

                    segments.append({
                        'clip': segment,
                        'start_time': start,
                        'end_time': end,
                        'speed_factor': speed_factor,
                        'original_path': path,
                        'style_preset': style_preset,
                        'transition': 'fade'  # default
                    })

                processed_clips.extend(segments)

            except Exception as e:
                print(f"Error processing {path}: {e}")
                continue

        return processed_clips

    def _calculate_speed_factor(self, velocity_mode, audio_analysis, index):
        tempo = audio_analysis.get('tempo', 120)
        if velocity_mode == "AI Auto":
            return np.clip(1.0 + (tempo-120)/120, 0.5, 2.0)
        elif velocity_mode == "Beat Sync":
            return 1.0 + 0.3*np.sin(index)
        elif velocity_mode == "Smooth":
            return 1.0
        elif velocity_mode == "Aggressive":
            return random.choice([0.5, 0.7, 1.5, 2.0])
        return 1.0

    def add_effects(self, processed_clips, enable_text_overlays, enable_effects, style_preset):
        """Apply effects and optional text overlays to all clips"""
        final_segments = []
        for seg in processed_clips:
            clip = seg['clip']

            # Dummy visual effect
            if enable_effects:
                clip = clip.fx(vfx.lum_contrast, 0, 50, 128)

            # Text overlay
            if enable_text_overlays:
                txt = TextClip("Monet AI", fontsize=30, color='white')
                txt = txt.set_duration(clip.duration).set_position(('center', 'bottom'))
                clip = CompositeVideoClip([clip, txt])

            seg['clip'] = clip
            final_segments.append(seg)

        return final_segments
