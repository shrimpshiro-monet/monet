import imageio
imageio.plugins.ffmpeg.download()  # ensures ffmpeg binaries are available
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx
import numpy as np
import random


class VideoProcessor:
    def __init__(self):
        self.clips_cache = []

    def process_clips(self, video_paths, audio_analysis, style_preset, velocity_mode, transition_intensity):
        """Cut and process video clips based on audio beats and style"""
        processed_clips = []
        beats = audio_analysis.get('beats', [])
        if len(beats) < 2:
            beats = np.linspace(0, audio_analysis.get('duration', 30), 10)

        for i, path in enumerate(video_paths):
            try:
                clip = VideoFileClip(path)
                
                # Optional reverse
                if random.random() < 0.15:  # 15% chance
                    clip = clip.fx(vfx.time_mirror)

                # Speed adjustment based on velocity mode
                speed_factor = self._calculate_speed_factor(velocity_mode, audio_analysis, i)
                clip = clip.fx(vfx.speedx, speed_factor)

                processed_clips.append({
                    'clip': clip,
                    'original_path': path,
                    'speed_factor': speed_factor,
                    'style_preset': style_preset
                })
            except Exception as e:
                print(f"Error processing {path}: {e}")
                continue

        return processed_clips

    def _calculate_speed_factor(self, velocity_mode, audio_analysis, clip_index):
        """Determine playback speed based on mode"""
        tempo = audio_analysis.get('tempo', 120)
        if velocity_mode == "AI Auto":
            return np.clip(1.0 + (tempo-120)/120, 0.5, 2.0)
        elif velocity_mode == "Beat Sync":
            return 1.0 + 0.5*np.sin(clip_index)  # dummy sync
        elif velocity_mode == "Smooth":
            return 1.0
        elif velocity_mode == "Aggressive":
            return random.choice([0.5, 0.7, 1.5, 2.0])
        else:
            return 1.0

    def add_effects(self, final_video, enable_text_overlays, enable_effects, style_preset):
        """Apply effects on a final VideoFileClip"""
        clip = final_video['clip'] if isinstance(final_video, dict) else final_video

        if enable_effects:
            clip = clip.fx(vfx.lum_contrast, 0, 50, 128)  # dummy effect

        # For text overlays, you can use clip = clip.fx(vfx.add_text, "Hello") etc.

        final_video['clip'] = clip
        return final_video
