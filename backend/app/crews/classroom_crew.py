from crewai import Crew, Process

from app.agents.teacher_agent import TeacherAgent
from app.agents.student_agent import StudentAgent
from app.agents.summary_agent import SummaryAgent

from app.tasks.teacher_task import TeacherTask
from app.tasks.student_task import StudentTask
from app.tasks.summary_task import SummaryTask


class ClassroomCrew:

    def build(self):

        teacher = TeacherAgent().build()
        student = StudentAgent().build()
        summary = SummaryAgent().build()

        teacher_task = TeacherTask().build()
        student_task = StudentTask().build()
        summary_task = SummaryTask().build()

        return Crew(
            agents=[
                teacher,
                student,
                summary
            ],
            tasks=[
                teacher_task,
                student_task,
                summary_task
            ],
            process=Process.sequential,
            verbose=True
        )