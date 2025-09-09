# main_codes/monet_audioanalyzer.py
import librosa
import numpy as np

class AudioAnalyzer:
    def analyze_audio(self, audio_path):
        """
        Analyze the audio and return:
        - duration
        - beats (timestamps in seconds)
        - tempo (BPM)
        - energy_levels (optional for speed factors)
        """
        y, sr = librosa.load(audio_path, sr=None, mono=True)  # Load audio as mono
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units='frames')
        
        # Convert beat frames to time in seconds
        beats = librosa.frames_to_time(beat_frames, sr=sr).tolist()

        # Compute energy (RMS)
        hop_length = 512
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        # Normalize energy
        energy_levels = (rms / np.max(rms)).tolist() if len(rms) > 0 else [1.0] * len(beats)

        duration = librosa.get_duration(y=y, sr=sr)

        return {
            "duration": duration,
            "beats": beats,
            "tempo": tempo,
            "energy_levels": energy_levels
        }
