from crewai import Agent


class NotesAgent:

    def build(self):

        return Agent(

            role="Smart Notes Generator",

            goal="""
Convert lectures into concise,
well-structured study notes.
""",

            backstory="""
Expert in summarization,
note organization,
and revision material preparation.
""",

            verbose=True,
           memory=True,
           allow_delegation=False
        )