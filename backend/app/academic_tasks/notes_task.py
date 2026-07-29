from crewai import Task
from app.agents.academic_agents.notes_agent import NotesAgent


class NotesTask:

    def build(self):

        return Task(

            description="""
Generate classroom notes.

Include:

• Summary
• Key Concepts
• Definitions
• Examples
• Revision Points
""",

            expected_output="""
Structured classroom notes.
""",

            agent=NotesAgent().build()
        )