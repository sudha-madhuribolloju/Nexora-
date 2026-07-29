from crewai import Task
from app.agents.platform_agents.voicerecognition_agent import VoiceRecognitionAgent


class VoiceRecognitionTask:

    def build(self):

        return Task(

            description="""
Analyze classroom audio.

Perform:

• Teacher Identification
• Student Identification
• Speaker Timeline
• Confidence Scores
• Voice Summary
""",

            expected_output="Voice recognition report.",

            agent=VoiceRecognitionAgent().build()
        )