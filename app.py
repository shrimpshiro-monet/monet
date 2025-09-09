import streamlit as st
import os
import tempfile
import time
import numpy as np
from pathlib import Path
import shutil
import subprocess

from main_codes.monet_videoprocessor import VideoProcessor
from main_codes.monet_audioanalyzer import AudioAnalyzer
from main_codes.monet_exportmanager import ExportManager
from main_codes.monet_transitionengine import TransitionEngine

# ---------------------------
# Ensure ffmpeg exists for MoviePy
# ---------------------------
FFMPEG_BIN = os.path.join(tempfile.gettempdir(), "ffmpeg")
if not os.path.exists(FFMPEG_BIN):
    try:
        # Download static ffmpeg binary for Linux (Streamlit Cloud)
        import requests
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz"
        tmp_archive = os.path.join(tempfile.gettempdir(), "ffmpeg.tar.xz")
        r = requests.get(url, stream=True)
        with open(tmp_archive, "wb") as f:
            shutil.copyfileobj(r.raw, f)
        # Extract and copy ffmpeg binary
        import tarfile
        with tarfile.open(tmp_archive) as tar:
            for member in tar.getmembers():
                if "ffmpeg" in member.name and not member.isdir():
                    tar.extract(member, path=tempfile.gettempdir())
                    shutil.move(os.path.join(tempfile.gettempdir(), member.name), FFMPEG_BIN)
        os.chmod(FFMPEG_BIN, 0o755)
    except Exception as e:
        st.error(f"⚠️ Failed to setup ffmpeg: {e}")

# Tell MoviePy to use our ffmpeg
os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_BIN

# ---------------------------
# Initialize session state
# ---------------------------
for key, default in {
    "video_processor": VideoProcessor(),
    "audio_analyzer": AudioAnalyzer(),
    "export_manager": ExportManager(),
    "transition_engine": TransitionEngine(),
    "uploaded_videos": [],
    "uploaded_audio": None,
    "reference_video": None,
    "processed_project": None,
    "export_count": 0,
    "editing_clip": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------
# Streamlit App
# ---------------------------
def main():
    st.set_page_config(
        page_title="Monet - AI Video Editor",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🎬 Monet - AI Video Editor")
    st.subheader("Professional AI-Powered Video Editing with 50+ Transitions")

    sidebar()
    main_area()

# ---------------------------
# Sidebar: Uploads & Settings
# ---------------------------
def sidebar():
    with st.sidebar:
        st.header("📁 Upload Media")
        uploaded_videos = st.file_uploader(
            "Upload video clips (MP4)", type=['mp4'], accept_multiple_files=True
        )
        if uploaded_videos:
            st.session_state.uploaded_videos = uploaded_videos
            st.success(f"✅ {len(uploaded_videos)} video(s) uploaded")

        uploaded_audio = st.file_uploader(
            "Upload music file (MP3, WAV)", type=['mp3', 'wav']
        )
        if uploaded_audio:
            st.session_state.uploaded_audio = uploaded_audio
            st.success("✅ Audio uploaded")

        reference_video = st.file_uploader(
            "Upload reference video (Optional)", type=['mp4']
        )
        if reference_video:
            st.session_state.reference_video = reference_video
            st.success("✅ Reference video uploaded")

        # Style & settings
        st.header("🎨 Style Settings")
        style_preset = st.selectbox(
            "Style Preset",
            ["Viral TikTok", "Cinematic", "Energetic", "Smooth", "Glitch", "Retro", "Custom"]
        )
        velocity_mode = st.selectbox(
            "Velocity Mode",
            ["AI Auto", "Beat Sync", "Smooth", "Aggressive", "Custom"]
        )
        transition_intensity = st.slider("Transition Intensity", 1, 10, 7)
        enable_text_overlays = st.checkbox("Enable Text Overlays", True)
        enable_effects = st.checkbox("Enable Visual Effects", True)
        enable_reverse_clips = st.checkbox("Enable Reverse Clips", True)

        if st.button("🚀 Process Video"):
            if not st.session_state.uploaded_videos or not st.session_state.uploaded_audio:
                st.error("Upload at least one video and an audio file")
            else:
                process_video(
                    style_preset, velocity_mode, transition_intensity,
                    enable_text_overlays, enable_effects, enable_reverse_clips
                )

# ---------------------------
# Main content area
# ---------------------------
def main_area():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.header("🎬 Timeline & Preview")
        if st.session_state.processed_project:
            display_timeline_preview()
        else:
            st.info("Upload media and click 'Process Video'")
            show_upload_status()
    with col2:
        export_section()

# ---------------------------
# Helper UI functions
# ---------------------------
def show_upload_status():
    if st.session_state.uploaded_videos:
        st.write("📹 Uploaded Videos:")
        for vid in st.session_state.uploaded_videos:
            st.write(f"• {vid.name}")
    if st.session_state.uploaded_audio:
        st.write(f"🎵 Uploaded Audio: {st.session_state.uploaded_audio.name}")

def export_section():
    st.header("📤 Export")
    export_quality = st.selectbox("Export Quality", ["Low (480p)", "Medium (720p)", "High (1080p)", "Ultra (4K)"])
    max_exports = 3
    export_disabled = st.session_state.export_count >= max_exports
    if export_disabled:
        st.warning("🔒 Free users limited to 3 exports.")
    if st.button("🎬 Export Video", disabled=not st.session_state.processed_project or export_disabled):
        export_video(export_quality)

# ---------------------------
# Core processing
# ---------------------------
def process_video(style_preset, velocity_mode, transition_intensity, enable_text_overlays, enable_effects, enable_reverse_clips):
    progress = st.progress(0)
    status = st.empty()
    try:
        # Save uploaded files safely
        status.text("Saving uploaded media...")
        video_paths = []
        for vid in st.session_state.uploaded_videos:
            tmp_path = os.path.join(tempfile.gettempdir(), vid.name)
            with open(tmp_path, "wb") as f:
                f.write(vid.getbuffer())
            video_paths.append(tmp_path)

        audio_path = None
        if st.session_state.uploaded_audio:
            audio = st.session_state.uploaded_audio
            audio_path = os.path.join(tempfile.gettempdir(), audio.name)
            with open(audio_path, "wb") as f:
                f.write(audio.getbuffer())

        progress.progress(10)
        status.text("Analyzing audio...")
        audio_analysis = st.session_state.audio_analyzer.analyze_audio(audio_path)
        progress.progress(30)
        status.text("Processing video clips...")
        processed_clips = st.session_state.video_processor.process_clips(
            video_paths, audio_analysis, style_preset, velocity_mode, transition_intensity
        )
        progress.progress(60)
        status.text("Applying transitions...")
        final_video = st.session_state.transition_engine.apply_transitions(
            processed_clips, audio_analysis, style_preset, transition_intensity
        )
        progress.progress(80)
        if enable_effects or enable_text_overlays:
            status.text("Adding effects & overlays...")
            final_video = st.session_state.video_processor.add_effects(
                final_video, enable_text_overlays, enable_effects, style_preset
            )
        st.session_state.processed_project = final_video
        progress.progress(100)
        status.text("✅ Processing complete!")
        time.sleep(1)
        progress.empty()
        status.empty()
        st.rerun()
    except Exception as e:
        st.error(f"Error processing video: {e}")
        progress.empty()
        status.empty()

# ---------------------------
# Timeline & clip preview
# ---------------------------
def display_timeline_preview():
    project = st.session_state.processed_project
    st.subheader("🎵 Audio Timeline")
    audio_analysis = getattr(project, 'audio_analysis', None) or {"beats": np.linspace(0, 30, 10), "duration":30}
    beats = audio_analysis.get("beats", [])
    duration = int(audio_analysis.get("duration", 30))
    timeline = np.zeros(duration*10)
    for b in beats:
        idx = min(int(b*10), len(timeline)-1)
        timeline[idx] = 1
    st.line_chart(timeline)

    st.subheader("📹 Clips")
    clips = getattr(project, "clips", []) or []
    for i, clip in enumerate(clips):
        with st.expander(f"Clip {i+1}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"Start: {clip.get('start_time',0):.2f}s")
                st.write(f"Duration: {clip.get('duration',0):.2f}s")
            with col2:
                st.write(f"Transition: {clip.get('transition','None')}")
                st.write(f"Speed: {clip.get('speed_factor',1.0)}x")
            with col3:
                if st.button(f"Edit Clip {i+1}", key=f"edit_clip_{i}"):
                    edit_clip(i)

def edit_clip(clip_index):
    st.session_state.editing_clip = clip_index
    st.rerun()

def export_video(quality):
    if not st.session_state.processed_project:
        st.error("No processed video to export")
        return
    progress = st.progress(0)
    status = st.empty()
    try:
        status.text("Exporting video...")
        output_path = st.session_state.export_manager.export_video(
            st.session_state.processed_project, quality, progress_callback=lambda p: progress.progress(p)
        )
        st.session_state.export_count += 1
        status.text("✅ Export complete!")

        with open(output_path, 'rb') as f:
            st.download_button(
                label="📥 Download Video",
                data=f.read(),
                file_name=f"monet_export_{int(time.time())}.mp4",
                mime="video/mp4"
            )
        progress.empty()
        status.empty()
    except Exception as e:
        st.error(f"Export failed: {e}")
        progress.empty()
        status.empty()

# ---------------------------
if __name__ == "__main__":
    main()
