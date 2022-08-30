from django.urls import path
from django.contrib import admin

import quality_control.views.api as api
import quality_control.views.control_views as cv

admin.autodiscover()


urlpatterns = [
    path('new/', cv.NewControlView.as_view(), name='new_control'),
    path('homework/<int:pk>/evaluate/', api.GetVideoClaseView.as_view(), name='api_get_videoclase'),
    path('homework/<int:pk>/evaluate-teacher/', api.GetVideoClaseTeacherView.as_view(),
        name='api_get_videoclase_teacher'),
    path('homework/<int:homework_id>/evaluations/',
        api.descargar_homework_evaluation,
        name='descargar_homework_evaluations'),
    path('homework/<int:homework_id>/evaluations-teacher/',
        api.descargar_teacher_evaluations,
        name='descargar_teacher_evaluations'),
]