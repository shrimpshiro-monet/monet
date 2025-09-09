# main_codes/monet_transitionengine.py
from moviepy.editor import concatenate_videoclips

class TransitionEngine:
    def __init__(self):
        # transition_library can be expanded with more transition functions
        self.transition_library = {
            'fade': self._fade_transition,
            'slide': self._slide_transition
        }

    def _fade_transition(self, clip1, clip2, duration=0.5):
        """Simple fadeout/fadein between two clips"""
        return clip1.crossfadeout(duration).set_end(clip1.duration)

    def _slide_transition(self, clip1, clip2, duration=0.5):
        """Dummy placeholder: currently just concatenates"""
        return clip1.set_end(clip1.duration)

    def apply_transitions(self, processed_clips, audio_analysis, style_preset, transition_intensity):
        """
        Takes a list of clip dicts from VideoProcessor, applies transitions, and returns
        a dict with 'clips' and 'final_video' ready for effects
        """
        if not processed_clips:
            return None

        final_clips = []
        for i, clip_dict in enumerate(processed_clips):
            clip = clip_dict['clip']
            # assign a transition type (random for demo, can be smarter)
            transition_type = 'fade'  # you can randomize or style-based
            clip_dict['transition'] = transition_type
            final_clips.append(clip)

        # concatenate clips with crossfade
        try:
            if len(final_clips) > 1:
                # Apply simple fade transitions
                final_video = concatenate_videoclips(final_clips, method="compose", padding=-0.1)
            else:
                final_video = final_clips[0]
        except Exception as e:
            print(f"Error applying transitions: {e}")
            final_video = final_clips[0]

        return {
            'clips': processed_clips,
            'final_video': final_video
        }
