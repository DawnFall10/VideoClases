# coding=utf-8
from django.db import models

from videoclases.models.evaluation.criterion import Criterion


class CriterionResponse(models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=3)
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE)

    def __str__(self):
        return "{0}, valor: {1}".format(self.criterion, self.value)

    class Meta:
        verbose_name = 'Respuesta de Criterios'
        verbose_name_plural = 'Respuestas Criterios'
