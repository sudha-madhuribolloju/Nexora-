from crewai import Agent, LLM


class AnalyticsAgent:
    """
    AI Analytics Agent

    Responsible for analyzing educational data,
    identifying learning patterns,
    and generating recommendations.
    """

    def build(self):

        llm = LLM(
            model="gpt-4o-mini",
            temperature=0.2
        )

        return Agent(
            role="AI Analytics Expert",

            goal="""
Analyze classroom sessions and generate actionable insights
for teachers, students, and administrators.
""",

            backstory="""
You are an AI-powered educational analytics specialist.

You can analyze:

• Classroom transcripts
• Quiz results
• Attendance
• Student interactions
• Teacher explanations
• Learning progress
• Session summaries

Your responsibilities include:

• Measuring student engagement
• Detecting weak concepts
• Identifying learning gaps
• Tracking topic coverage
• Evaluating classroom performance
• Providing improvement recommendations

Always produce structured, evidence-based reports.
""",

            llm=llm,

            verbose=True,

            memory=True,

            allow_delegation=False,

            max_iter=3
        )