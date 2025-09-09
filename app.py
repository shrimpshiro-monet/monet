import streamlit as st
import os
import tempfile
import time
import numpy as np
from pathlib import Path

# Import your actual engines
from main_codes.monet_videoprocessor import VideoProcessor
from main_codes.monet_audioanalyzer import AudioAnalyzer
from main_codes.monet_exportmanager import ExportManager
from main_codes.monet_transitionengine import TransitionEngine

# ---------------------------
# Initialize session state
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
if 'reference_video' not in st.session_state:
    st.session_state.reference_video = None
if 'processed_project' not in st.session_state:
    st.session_state.processed_project = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'export_count' not in st.session_state:
    st.session_state.export_count = 0
if 'editing_clip' not in st.session_state:
    st.session_state.editing_clip = None

# ---------------------------
# Main Streamlit App
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
# Sidebar for uploads & settings
# ---------------------------
def sidebar():
    with st.sidebar:
        st.header("📁 Upload Media")

        uploaded_videos = st.file_uploader(
            "Upload video clips (MP4)", type=['mp4'], accept_multiple_files=True, key="video_uploader"
        )
        if uploaded_videos:
            st.session_state.uploaded_videos = uploaded_videos
            st.success(f"✅ {len(uploaded_videos)} video(s) uploaded")

        uploaded_audio = st.file_uploader(
            "Upload music file (MP3, WAV)", type=['mp3', 'wav'], key="audio_uploader"
        )
        if uploaded_audio:
            st.session_state.uploaded_audio = uploaded_audio
            st.success("✅ Audio uploaded")

        reference_video = st.file_uploader(
            "Upload reference video (Optional)", type=['mp4'], key="reference_uploader"
        )
        if reference_video:
            st.session_state.reference_video = reference_video
            st.success("✅ Reference video uploaded")

        # Style & editing settings
        st.header("🎨 Style Settings")
        style_preset = st.selectbox(
            "Style Preset",
            ["Viral TikTok", "Cinematic", "Energetic", "Smooth", "Glitch", "Retro", "Custom"]
        )
        velocity_mode = st.selectbox(
            "Velocity Mode",
            ["AI Auto", "Beat Sync", "Smooth", "Aggressive", "Custom"]
        )
        transition_intensity = st.slider("Transition Intensity", min_value=1, max_value=10, value=7)
        enable_text_overlays = st.checkbox("Enable Text Overlays", value=True)
        enable_effects = st.checkbox("Enable Visual Effects", value=True)
        enable_reverse_clips = st.checkbox("Enable Reverse Clips", value=True)

        if st.button("🚀 Process Video", use_container_width=True):
            if not st.session_state.uploaded_videos or not st.session_state.uploaded_audio:
                st.error("Please upload at least one video and an audio file")
            else:
                process_video(
                    style_preset,
                    velocity_mode,
                    transition_intensity,
                    enable_text_overlays,
                    enable_effects,
                    enable_reverse_clips,
                    st.session_state.reference_video
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
            st.info("Upload media and click 'Process Video' to see timeline and preview")
            show_upload_status()

    with col2:
        export_section()

# ---------------------------
# Helper UI functions
# ---------------------------
def show_upload_status():
    if st.session_state.uploaded_videos:
        st.write("📹 Uploaded Videos:")
        for video in st.session_state.uploaded_videos:
            st.write(f"• {video.name}")
    if st.session_state.uploaded_audio:
        st.write(f"🎵 Uploaded Audio: {st.session_state.uploaded_audio.name}")

def export_section():
    st.header("📤 Export")
    export_quality = st.selectbox("Export Quality", ["Low (480p)", "Medium (720p)", "High (1080p)", "Ultra (4K)"])
    is_premium = False
    max_exports = 3 if not is_premium else float('inf')
    export_disabled = st.session_state.export_count >= max_exports and not is_premium

    if export_disabled:
        st.warning("🔒 Free users limited to 3 exports. Upgrade for unlimited exports.")

    if st.button("🎬 Export Video", disabled=not st.session_state.processed_project or export_disabled, use_container_width=True):
        export_video(export_quality)

# ---------------------------
# Core processing
# ---------------------------
def process_video(style_preset, velocity_mode, transition_intensity, enable_text_overlays, enable_effects, enable_reverse_clips, reference_video):
    progress_bar = st.progress(0)
    status_text = st.empty()
    try:
        # Save uploaded files
        status_text.text("Saving uploaded media...")
        video_paths = []
        for video in st.session_state.uploaded_videos:
            temp_path = os.path.join(tempfile.gettempdir(), video.name)
            with open(temp_path, "wb") as f:
                f.write(video.getbuffer())
            video_paths.append(temp_path)

        audio_path = None
        if st.session_state.uploaded_audio:
            audio = st.session_state.uploaded_audio
            audio_path = os.path.join(tempfile.gettempdir(), audio.name)
            with open(audio_path, "wb") as f:
                f.write(audio.getbuffer())

        progress_bar.progress(10)

        # Analyze audio
        status_text.text("Analyzing audio...")
        audio_analysis = st.session_state.audio_analyzer.analyze_audio(audio_path)
        progress_bar.progress(30)

        # Process video clips
        status_text.text("Processing video clips...")
        processed_clips = st.session_state.video_processor.process_clips(
            video_paths, audio_analysis, style_preset, velocity_mode, transition_intensity
        )
        progress_bar.progress(60)

        # Apply transitions
        status_text.text("Applying transitions...")
        final_video = st.session_state.transition_engine.apply_transitions(
            processed_clips, audio_analysis, style_preset, transition_intensity
        )
        progress_bar.progress(80)

        # Add effects
        if enable_effects or enable_text_overlays:
            status_text.text("Adding effects & overlays...")
            final_video = st.session_state.video_processor.add_effects(
                final_video, enable_text_overlays, enable_effects, style_preset
            )

        # Save final project
        st.session_state.processed_project = final_video
        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        st.rerun()

    except Exception as e:
        st.error(f"Error processing video: {e}")
        progress_bar.empty()
        status_text.empty()

def display_timeline_preview():
    project = st.session_state.processed_project
    st.subheader("🎵 Audio Timeline")
    # Simple visual for now
    duration = 30
    timeline_data = np.zeros(duration*10)
    st.line_chart(timeline_data)

    st.subheader("📹 Clips")
    # If processed clips exist
    clips = getattr(project, 'clips', None) or []
    for i, clip in enumerate(clips):
        with st.expander(f"Clip {i+1}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"Start: {clip.get('start_time', 0):.2f}s")
                st.write(f"Duration: {clip.get('duration', 0):.2f}s")
            with col2:
                st.write(f"Transition: {clip.get('transition', 'None')}")
                st.write(f"Speed: {clip.get('speed_factor', 1.0)}x")
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
    progress_bar = st.progress(0)
    status_text = st.empty()
    try:
        status_text.text("Exporting video...")
        output_path = st.session_state.export_manager.export_video(
            st.session_state.processed_project, quality, progress_callback=lambda p: progress_bar.progress(p)
        )
        st.session_state.export_count += 1
        status_text.text("✅ Export complete!")

        with open(output_path, 'rb') as f:
            st.download_button(
                label="📥 Download Video",
                data=f.read(),
                file_name=f"monet_export_{int(time.time())}.mp4",
                mime="video/mp4"
            )
        progress_bar.empty()
        status_text.empty()
    except Exception as e:
        st.error(f"Export failed: {e}")
        progress_bar.empty()
        status_text.empty()

# ---------------------------
if __name__ == "__main__":
    main()
