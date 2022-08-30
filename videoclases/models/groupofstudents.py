from django.db import models

from videoclases.models.homework import Homework
from videoclases.models.student import Student


class GroupOfStudents(models.Model):
    number = models.IntegerField()
    homework = models.ForeignKey(Homework, related_name='groups', on_delete=models.CASCADE)
    students = models.ManyToManyField(Student)

    class Meta:
        unique_together = (('number', 'homework'),)

        verbose_name = 'Grupo de estudiantes'
        verbose_name_plural = 'Grupos de estudiantes'

    def __str__(self):
        return 'Course: ' + self.homework.course.name + '. Homework: ' + \
               self.homework.title + '. GroupOfStudents: ' + str(self.number)

    def display_students(self):
        return ', '.join([student.get_full_name() for student in self.students.all()])

    display_students.short_description = 'Students'
