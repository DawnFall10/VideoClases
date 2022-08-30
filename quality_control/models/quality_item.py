# coding=utf-8
from django.db import models

from videoclases.models.teacher import Teacher
from videoclases.models.video_clase import VideoClase
from .quality_score import QualityScore


class QualityItem(models.Model):
    videoclase = models.ForeignKey(VideoClase, related_name='qualityItemList', on_delete=models.CASCADE)
    score_check = models.ManyToManyField(QualityScore)
    teacher = models.ForeignKey(Teacher, default=2, on_delete=models.CASCADE)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return u"{0}".format(self.videoclase.question[:50])

    def get_evaluation(self):
        if self.score_check.count() > 0:
            result = list()
            for c in self.score_check.select_related('criteria'):
                result.append(
                    {'id': c.criteria.id, 'name': c.criteria.value, 'value': c.score}
                )
            return result
        return []

    def get_score(self):
        if self.score_check.count() > 0:
            return [c.score for c in self.score_check.select_related('criteria').order_by('criteria')]
        return []
