from crewai import Task
from app.agents.research_agent import ResearchAgent


class ResearchTask:

    def build(self):

        researcher = ResearchAgent().build()

        return Task(

            description="""
Research the requested academic topic.

Provide:

• Overview
• Detailed explanation
• Examples
• Applications
• References
""",

            expected_output="""
A structured research report.
""",

            agent=researcher
        )