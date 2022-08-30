from django.db import models

from videoclases.models.groupofstudents import GroupOfStudents
from videoclases.models.student import Student


class FinalScores(models.Model):
    group = models.ForeignKey(GroupOfStudents, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_score = models.FloatField(default=0, blank=True, null=True)
    teacher_score = models.FloatField(default=0)

    def ponderar_notas(self):
        return self.teacher_score

    def __str__(self):
        return 'Curso: ' + self.group.homework.course.name + '. Tarea: ' + \
        self.group.homework.title + '. Grupo: ' + str(self.group.number) + \
        '. Nota: ' + str(self.ponderar_notas())

    def group_number(self):
        return self.group.number

    group_number.short_description = '# de grupo'
    group_number.admin_order_field = 'group__number'

    def get_homework(self):
        return self.group.homework.title

    get_homework.short_description = 'Tarea'
    get_homework.admin_order_field = 'group__homework'

    def get_course(self):
        return self.group.homework.course

    get_course.short_description = 'Curso'
    get_course.admin_order_field = 'group__homework__course'

    class Meta:
        verbose_name = 'Nota final'
        verbose_name_plural = 'Notas finales'
