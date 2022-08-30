# coding=utf-8
from django.db import models

from videoclases.models.evaluation.criterion import Criterion
from videoclases.models.teacher import Teacher


class CriteriaByTeacher(models.Model):
    name = models.CharField(max_length=150,null=True, blank=True)
    criteria = models.ManyToManyField(Criterion)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    def __str__(self):
        if self.name:
            return str(self.name)
        return "Listado creado por profesor(a) {0}".format(self.teacher)

    class Meta:
        verbose_name = 'Criterio de evaluación'
        verbose_name_plural = 'Criterios de evaluación'
