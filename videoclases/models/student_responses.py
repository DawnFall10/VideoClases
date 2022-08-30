from django.db import models

from videoclases.models.student import Student
from videoclases.models.video_clase import VideoClase


class StudentResponses(models.Model):
    videoclase = models.ForeignKey(VideoClase, related_name='answers', on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    answer = models.CharField(max_length=100, blank=True, null=True)

    def is_correct(self):
        return self.answer == self.videoclase.correct_alternative

    def __str__(self):
        return 'Responde: ' + self.student.user.first_name + '. Respuesta: ' + str(self.answer) + \
        ' .Videoclase ' + str(self.videoclase.id) + ' ' + self.videoclase.homework.title

    def display_homework(self):
        return self.videoclase.homework.title

    display_homework.short_description = 'Homework'

    display_homework.admin_order_field = 'self.videoclase.homework'
    is_correct.short_description = 'Correct?'
    is_correct.boolean = True

    class Meta:
        verbose_name = 'Respuesta de estudiante'
        verbose_name_plural = 'Respuestas de estudiantes'
