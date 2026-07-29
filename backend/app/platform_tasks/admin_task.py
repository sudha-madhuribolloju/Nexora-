from crewai import Task
from app.agents.platform_agents.admin_agent import AdminAgent


class AdminTask:

    def build(self):

        return Task(

            description="""
Analyze platform administration activities.

Generate:

• Active Users
• New Registrations
• System Health
• Security Alerts
• Admin Recommendations
""",

            expected_output="Platform administration report.",

            agent=AdminAgent().build()
        )