from crewai import Agent


class SessionManagerAgent:

    def build(self):

        return Agent(

            role="Classroom Session Manager",

            goal="""
Manage classroom sessions from start to finish,
ensuring all AI services operate correctly.
""",

            backstory="""
You coordinate:

• Session start
• Session end
• Attendance
• Transcript generation
• AI agents
• Session metadata

Ensure every classroom session is recorded accurately.
""",

            verbose=True,
            memory=True,
            allow_delegation=False
        )