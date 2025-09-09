# main_codes/monet_exportmanager.py
import tempfile

class ExportManager:
    def export_video(self, processed_project, quality, progress_callback=None):
        clip = processed_project.get('clip')
        if not clip:
            raise ValueError("No clip to export")

        resolutions = {
            "Low (480p)": (854, 480),
            "Medium (720p)": (1280, 720),
            "High (1080p)": (1920, 1080),
            "Ultra (4K)": (3840, 2160)
        }
        w, h = resolutions.get(quality, (1280,720))
        clip_resized = clip.resize(newsize=(w,h))

        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        output_path = temp_file.name
        temp_file.close()

        clip_resized.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=4)
        return output_path
