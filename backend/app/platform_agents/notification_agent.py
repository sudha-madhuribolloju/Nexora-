from crewai import Agent


class NotificationAgent:

    def build(self):

        return Agent(

            role="Notification Manager",

            goal="""
Generate timely and relevant notifications for
students, teachers, and administrators.
""",

            backstory="""
You manage communication across the platform.

Notifications include:

• Assignment reminders
• Quiz alerts
• Attendance alerts
• Session reminders
• Exam schedules
• Announcements

Always avoid duplicate notifications.
""",

            verbose=True,
            memory=True,
            allow_delegation=False
        )