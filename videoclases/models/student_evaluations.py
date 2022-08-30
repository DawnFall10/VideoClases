from django.db import models
from django.utils import timezone

from videoclases.models.evaluation.criterion_response import CriterionResponse
from videoclases.models.student import Student
from videoclases.models.video_clase import VideoClase


class StudentEvaluations(models.Model):
    evaluations = (
        ("No me gusta", -1),
        ("Neutro", 0),
        ("Me gusta", 1),
    )

    # DEPRECATED
    scores = [
        ("No cumple el criterio", 0),
        ("Cumple muy parcialmente el criterio", 0.3),
        ("Cumple parcialmente el criterio", 0.5),
        ("Cumple en su gran mayoria el criterio", 0.8),
        ("Cumple el criterio", 1),
    ]

    author = models.ForeignKey(Student, on_delete=models.CASCADE)
    value = models.IntegerField(default=0)
    format = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    copyright = models.DecimalField(
        max_digits=2, decimal_places=1, null=True, blank=True
    )
    theme = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    pedagogical = models.DecimalField(
        max_digits=2, decimal_places=1, null=True, blank=True
    )
    rythm = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    originality = models.DecimalField(
        max_digits=2, decimal_places=1, null=True, blank=True
    )
    # END DEPRECATED

    criteria = models.ManyToManyField(CriterionResponse, blank=True)
    comments = models.TextField(default="", null=True, blank=True)
    videoclase = models.ForeignKey(
        VideoClase, related_name="evaluations", on_delete=models.CASCADE
    )
    created = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return "{0}, videoclase:{1}, {2}".format(
            self.author.user.get_full_name(),
            self.videoclase.id,
            self.videoclase.homework.full_name(),
        )

    def get_evaluation(self):
        if self.criteria.count() > 0:
            result = list()
            for c in self.criteria.select_related("criterion"):
                result.append(
                    {"id": c.criterion.id, "name": c.criterion.value, "value": c.value}
                )
            return result
        return [
            {"id": "originality", "name": "Originalidad", "value": self.originality},
            {"id": "format", "name": "Formato", "value": self.format},
            {"id": "copyright", "name": "Licencias", "value": self.copyright},
            {"id": "theme", "name": "Tema", "value": self.theme},
            {"id": "pedagogical", "name": "Pedagogía", "value": self.pedagogical},
            {"id": "rythm", "name": "Ritmo", "value": self.rythm},
        ]

    def get_score(self):
        return list(map(lambda x: x.get("value", 0), self.get_evaluation()))

    def get_score_name(self):
        return list(map(lambda x: x.get("name", ""), self.get_evaluation()))

    class Meta:
        verbose_name = "Evaluación de estudiante"
        verbose_name_plural = "Evaluaciones de estudiantes"
