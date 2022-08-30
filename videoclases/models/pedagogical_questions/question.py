from django.db import models

from videoclases.models.pedagogical_questions.alternative import Alternative


class Question(models.Model):
    question = models.CharField(max_length=255, blank=True, null=True)
    alternatives = models.ManyToManyField(Alternative, related_name='question_alternatives')
    correct = models.ForeignKey(Alternative, related_name='question_correct',
                                blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = 'Pregunta'
