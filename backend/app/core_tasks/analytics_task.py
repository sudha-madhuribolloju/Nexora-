from crewai import Task
from app.agents.analytics import AnalyticsAgent


class AnalyticsTask:

    def build(self):

        analytics = AnalyticsAgent().build()

        return Task(

            description="""
Analyze today's classroom session.

Evaluate:

• Student engagement
• Attendance
• Topic coverage
• Weak concepts
• Quiz performance
• Overall classroom performance

Generate actionable insights.
""",

            expected_output="""
A classroom analytics report containing:

- Executive Summary
- Engagement Score
- Weak Topics
- Student Performance
- Recommendations
""",

            agent=analytics
        )