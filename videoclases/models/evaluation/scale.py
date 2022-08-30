# coding=utf-8
from django.db import models

from videoclases.models.evaluation.scale_value import ScaleValue


class Scale(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    values = models.ManyToManyField(ScaleValue, blank=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Escala de Evaluación'
        verbose_name_plural = 'Escalas de Evaluación'
