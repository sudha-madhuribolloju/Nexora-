from crewai import Task
from app.agents.platform_agents.sessionmanager_agent import SessionManagerAgent


class SessionManagerTask:

    def build(self):

        return Task(

            description="""
Manage today's classroom session.

Handle:

• Session Initialization
• Attendance
• Audio Capture
• Session Monitoring
• Session Closure
""",

            expected_output="Complete session report.",

            agent=SessionManagerAgent().build()
        )