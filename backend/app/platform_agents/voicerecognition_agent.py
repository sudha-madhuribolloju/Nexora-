from crewai import Agent


class VoiceRecognitionAgent:

    def build(self):

        return Agent(

            role="Voice Recognition Specialist",

            goal="""
Recognize speakers and identify classroom participants
from audio recordings.
""",

            backstory="""
You specialize in:

• Speaker Identification
• Voice Fingerprinting
• Teacher Recognition
• Student Recognition
• Speaker Segmentation

Provide accurate speaker identification while maintaining
consistent labeling throughout the session.
""",

            verbose=True,
            memory=True,
            allow_delegation=False
        )