from crewai import Agent


class TranscriptProcessingAgent:

    def build(self):

        return Agent(

            role="Transcript Processing Expert",

            goal="""
Convert classroom transcripts into structured
educational content.
""",

            backstory="""
You clean, organize and process transcripts.

Generate:

• Clean Transcript
• Key Concepts
• Topics
• Action Items
• Speaker Identification
""",

            verbose=True,
            memory=True,
            allow_delegation=False
        )