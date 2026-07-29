from crewai import Task
from app.agents.summary_agent import SummaryAgent


class SummaryTask:

    def build(self):

        summarizer = SummaryAgent().build()

        return Task(

            description="""
Summarize today's lecture.

Generate:

• Summary
• Notes
• Key Concepts
• Important Definitions
• Revision Notes
""",

            expected_output="""
A well-structured lecture summary.
""",

            agent=summarizer
        )