from django.db import models

from videoclases.models.pedagogical_questions.alternative import Alternative
from videoclases.models.pedagogical_questions.question import Question


class Response(models.Model):
    question = models.ForeignKey(Question, related_name='response_question', on_delete=models.CASCADE)
    answer = models.ForeignKey(Alternative, related_name='answer_question', on_delete=models.CASCADE)

    def __str__(self):
        return u'{0} - {1}'.format(self.question, self.answer)

    class Meta:
        verbose_name = 'Respuesta'
