import datetime

from django.db import models

from videoclases.models.school import School


class Course(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    year = models.IntegerField(default=datetime.datetime.now().year)

    def __str__(self):
        return self.name + ' ' + str(self.year)

    class Meta:
        verbose_name = 'Curso'
        ordering = ['-year', '-id']
