# main_codes/monet_videoprocessor.py
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx
import numpy as np

class VideoProcessor:
    def __init__(self):
        self.clips_cache = []

    def process_clips(self, video_paths, audio_analysis, style_preset, velocity_mode, transition_intensity):
        """
        Cut video clips based on audio beats and style
        Returns list of clip dicts with processed VideoFileClip inside
        """
        processed_clips = []
        beats = audio_analysis.get('beats', [])
        duration = audio_analysis.get('duration', 30)

        if len(beats) < 2:
            # fallback if beats not detected
            beats = np.linspace(0, duration, 10)

        for path in video_paths:
            try:
                clip = VideoFileClip(path)
                clip_duration = clip.duration

                # Split clip by beats
                clip_starts = np.clip(beats, 0, clip_duration-0.01)
                clip_ends = np.append(clip_starts[1:], clip_duration)

                for start, end in zip(clip_starts, clip_ends):
                    subclip = clip.subclip(start, end)

                    # Optional reverse
                    if np.random.rand() < 0.15:
                        subclip = subclip.fx(vfx.time_mirror)

                    # Speed adjustment
                    speed_factor = self._calculate_speed_factor(velocity_mode, audio_analysis, start)
                    subclip = subclip.fx(vfx.speedx, speed_factor)

                    processed_clips.append({
                        'clip': subclip,
                        'start_time': start,
                        'duration': end-start,
                        'speed_factor': speed_factor,
                        'transition': None  # will be filled by TransitionEngine
                    })
            except Exception as e:
                print(f"Error processing {path}: {e}")
                continue

        return processed_clips

    def _calculate_speed_factor(self, velocity_mode, audio_analysis, clip_index):
        tempo = audio_analysis.get('tempo', 120)
        if velocity_mode == "AI Auto":
            return np.clip(1.0 + (tempo-120)/120, 0.5, 2.0)
        elif velocity_mode == "Beat Sync":
            return 1.0 + 0.5*np.sin(clip_index)
        elif velocity_mode == "Smooth":
            return 1.0
        elif velocity_mode == "Aggressive":
            return np.random.choice([0.5, 0.7, 1.5, 2.0])
        else:
            return 1.0

    def add_effects(self, final_video, enable_text_overlays, enable_effects, style_preset):
        """
        Apply effects to the final project.
        Expects final_video as dict with 'clips' or single VideoFileClip
        """
        if isinstance(final_video, dict):
            clips = final_video.get('clips', [])
            for i, clip_dict in enumerate(clips):
                clip = clip_dict['clip']
                if enable_effects:
                    clip = clip.fx(vfx.lum_contrast, 0, 50, 128)
                clip_dict['clip'] = clip
            final_video['clips'] = clips
        else:
            clip = final_video
            if enable_effects:
                clip = clip.fx(vfx.lum_contrast, 0, 50, 128)
            final_video = clip
        return final_video
