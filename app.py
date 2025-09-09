import streamlit as st
import os
import tempfile
import time
import numpy as np
import random

# Force MoviePy to detect ffmpeg
import imageio
import imageio_ffmpeg  # ensures ffmpeg binary is available

from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx
from pydub import AudioSegment

# ---------------------------
# Simulated / real engines
# ---------------------------
class VideoProcessor:
    def process_clips(self, video_paths, audio_analysis, style_preset, velocity_mode, transition_intensity):
        processed_clips = []
        beats = audio_analysis.get("beats", [])
        if len(beats) < 2:
            beats = np.linspace(0, audio_analysis.get("duration", 30), 10)

        for i, path in enumerate(video_paths):
            try:
                clip = VideoFileClip(path)

                # Optional reverse (15% chance)
                if random.random() < 0.15:
                    clip = clip.fx(vfx.time_mirror)

                # Speed factor
                speed_factor = self._calculate_speed(velocity_mode, i)
                clip = clip.fx(vfx.speedx, speed_factor)

                processed_clips.append({
                    "clip": clip,
                    "original_path": path,
                    "speed_factor": speed_factor,
                    "start_time": 0,
                    "duration": clip.duration,
                    "transition": "none",
                    "style_preset": style_preset
                })
            except Exception as e:
                print(f"Error processing {path}: {e}")
                continue
        return processed_clips

    def _calculate_speed(self, velocity_mode, clip_index):
        if velocity_mode == "AI Auto":
            return 1.0 + random.uniform(-0.1, 0.3)
        elif velocity_mode == "Beat Sync":
            return 1.0 + 0.5 * np.sin(clip_index)
        elif velocity_mode == "Smooth":
            return 1.0
        elif velocity_mode == "Aggressive":
            return random.choice([0.5, 0.7, 1.5, 2.0])
        return 1.0

    def add_effects(self, final_video, enable_text_overlays, enable_effects, style_preset):
        # dummy effect
        if enable_effects:
            final_video['clip'] = final_video['clip'].fx(vfx.lum_contrast, 0, 50, 128)
        return final_video

class AudioAnalyzer:
    def analyze_audio(self, audio_path):
        audio = AudioSegment.from_file(audio_path)
        duration = len(audio)/1000
        num_beats = max(5, int(duration/2))
        beats = np.linspace(0, duration, num_beats).tolist()
        return {
            "duration": duration,
            "beats": beats,
            "tempo": 120,
        }

class TransitionEngine:
    def apply_transitions(self, clips, audio_analysis, style_preset, transition_intensity):
        for clip in clips:
            clip["transition"] = random.choice(["fade", "slide", "none"])
        return {"clip": concatenate_videoclips([c["clip"] for c in clips]), "clips": clips}

class ExportManager:
    def export_video(self, project, quality, progress_callback):
        final_clip = project['clip']
        output_file = os.path.join(tempfile.gettempdir(), f"monet_export_{int(time.time())}.mp4")
        final_clip.write_videofile(output_file, codec="libx264")
        for p in range(0, 101, 20):
            time.sleep(0.2)
            progress_callback(p)
        return output_file

# ---------------------------
# Session state
# ---------------------------
if 'video_processor' not in st.session_state:
    st.session_state.video_processor = VideoProcessor()
if 'audio_analyzer' not in st.session_state:
    st.session_state.audio_analyzer = AudioAnalyzer()
if 'export_manager' not in st.session_state:
    st.session_state.export_manager = ExportManager()
if 'transition_engine' not in st.session_state:
    st.session_state.transition_engine = TransitionEngine()
if 'uploaded_videos' not in st.session_state:
    st.session_state.uploaded_videos = []
if 'uploaded_audio' not in st.session_state:
    st.session_state.uploaded_audio = None
if 'processed_project' not in st.session_state:
    st.session_state.processed_project = None
if 'export_count' not in st.session_state:
    st.session_state.export_count = 0

# ---------------------------
# Streamlit UI
# ---------------------------
def main():
    st.set_page_config(page_title="Monet AI Editor", page_icon="🎬", layout="wide")
    st.title("🎬 Monet - AI Video Editor")

    sidebar()
    main_area()

def sidebar():
    with st.sidebar:
        st.header("📁 Upload Media")
        uploaded_videos = st.file_uploader("Upload video clips (MP4)", type=['mp4'], accept_multiple_files=True)
        if uploaded_videos:
            st.session_state.uploaded_videos = uploaded_videos

        uploaded_audio = st.file_uploader("Upload audio (MP3/WAV)", type=['mp3','wav'])
        if uploaded_audio:
            st.session_state.uploaded_audio = uploaded_audio

        style_preset = st.selectbox("Style Preset", ["Viral TikTok","Cinematic","Energetic","Smooth","Glitch","Retro","Custom"])
        velocity_mode = st.selectbox("Velocity Mode", ["AI Auto","Beat Sync","Smooth","Aggressive","Custom"])
        transition_intensity = st.slider("Transition Intensity", 1, 10, 7)

        if st.button("🚀 Process Video"):
            if not st.session_state.uploaded_videos or not st.session_state.uploaded_audio:
                st.error("Upload at least one video and audio")
            else:
                process_video(style_preset, velocity_mode, transition_intensity)

def main_area():
    col1, col2 = st.columns([2,1])
    with col1:
        st.header("🎬 Preview")
        if st.session_state.processed_project:
            clips = st.session_state.processed_project.get('clips', [])
            for i, clip in enumerate(clips):
                st.write(f"Clip {i+1}: {clip['original_path']}, Duration: {clip['duration']:.2f}s")
        else:
            st.info("Upload media and process video to preview")
    with col2:
        export_section()

def export_section():
    if st.session_state.processed_project:
        if st.button("🎬 Export Video"):
            export_video()

# ---------------------------
# Core processing
# ---------------------------
def process_video(style_preset, velocity_mode, transition_intensity):
    progress = st.progress(0)
    try:
        video_paths = []
        for v in st.session_state.uploaded_videos:
            path = os.path.join(tempfile.gettempdir(), v.name)
            with open(path,"wb") as f:
                f.write(v.getbuffer())
            video_paths.append(path)

        audio_file = st.session_state.uploaded_audio
        audio_path = os.path.join(tempfile.gettempdir(), audio_file.name)
        with open(audio_path,"wb") as f:
            f.write(audio_file.getbuffer())

        progress.progress(10)
        st.info("Analyzing audio...")
        audio_analysis = st.session_state.audio_analyzer.analyze_audio(audio_path)
        progress.progress(30)

        st.info("Processing video clips...")
        clips = st.session_state.video_processor.process_clips(video_paths, audio_analysis, style_preset, velocity_mode, transition_intensity)
        progress.progress(60)

        st.info("Applying transitions...")
        final_project = st.session_state.transition_engine.apply_transitions(clips, audio_analysis, style_preset, transition_intensity)
        progress.progress(90)

        st.info("Adding effects...")
        final_project = st.session_state.video_processor.add_effects(final_project, True, True, style_preset)
        st.session_state.processed_project = final_project
        progress.progress(100)
        st.success("✅ Processing complete!")

    except Exception as e:
        st.error(f"Error: {e}")
        progress.empty()

def export_video():
    progress = st.progress(0)
    try:
        output_path = st.session_state.export_manager.export_video(st.session_state.processed_project, "High", lambda p: progress.progress(p))
        st.success("✅ Export complete!")
        with open(output_path,'rb') as f:
            st.download_button("📥 Download Video", f.read(), file_name=f"monet_export_{int(time.time())}.mp4", mime="video/mp4")
        progress.empty()
    except Exception as e:
        st.error(f"Export failed: {e}")
        progress.empty()

if __name__ == "__main__":
    main()
