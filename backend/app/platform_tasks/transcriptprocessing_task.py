from crewai import Task
from app.agents.platform_agents.transcriptprocessing_agent import TranscriptProcessingAgent


class TranscriptProcessingTask:

    def build(self):

        return Task(

            description="""
Process today's classroom transcript.

Perform:

• Cleaning
• Speaker Segmentation
• Topic Detection
• Concept Extraction
• Final Transcript Generation
""",

            expected_output="Structured classroom transcript.",

            agent=TranscriptProcessingAgent().build()
        )