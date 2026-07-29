from crewai import Task
from app.agents.platform_agents.notification_agent import NotificationAgent


class NotificationTask:

    def build(self):

        return Task(

            description="""
Prepare notifications for today's activities.

Include:

• Class reminders
• Assignment reminders
• Quiz notifications
• Attendance alerts
""",

            expected_output="Notification schedule.",

            agent=NotificationAgent().build()
        )