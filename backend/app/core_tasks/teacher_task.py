from crewai import Task
from app.agents.teacher_agent import TeacherAgent


class TeacherTask:

    def build(self):

        teacher = TeacherAgent().build()

        return Task(

            description="""
Assist the teacher during today's classroom.

Responsibilities:

• Explain concepts
• Answer student questions
• Recommend examples
• Suggest activities
• Generate homework
""",

            expected_output="""
Teaching assistant report containing:

- Concepts Explained
- Student Questions
- Homework
- Activities
- Recommendations
""",

            agent=teacher
        )