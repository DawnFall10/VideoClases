from django.urls import path, re_path
from django.contrib import admin
from django.contrib.auth import views as auth_views
import videoclases.views.homework as hw
import videoclases.views.pegadogical_questions as pq
import videoclases.views.views as vv

admin.autodiscover()

urlpatterns = [
    path('', vv.IndexView.as_view(), name='index'),
    path('organizer', vv.OrganizerView.as_view(), name='organizer'),

    path("password_reset", vv.password_reset_request, name="password_reset"),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'), 

    path('student/evaluate-conceptual-test-form/<int:pk>/',
        pq.ResponsePedagogicalQuestion.as_view(),
        name='evaluate_pedagogical_questions'),

    path('student/send-videoclase/<int:homework_id>/',
        vv.SendVideoclaseView.as_view(),
        name='send_videoclase'),
    path('student/review-video/',
        vv.StudentEvaluationsFormView.as_view(),
        name='evaluar_video'),
    path('student/review-videoclase/<int:homework_id>/',
        vv.StudentResponsesView.as_view(),
        name='review_videoclase'),
    path('student/review-videoclase-form/',
        vv.StudentResponsesFormView.as_view(),
        name='review_videoclase_form'),
    path('student/watch-videoclase/<int:homework_id>/',
        vv.VideoclaseDetailView.as_view(),
        name='watch_videoclase'),
    re_path(r'^student/',
        vv.StudentView.as_view(),
        name='student'),
    re_path(r'^change-password/',
        vv.ChangePasswordView.as_view(),
        name='change_password'),
    path('change-password-student/<int:course_id>/',
        vv.ChangeStudentPasswordView.as_view(),
        name='change_student_password'),
    re_path(r'^change-password-student/',
        vv.ChangeStudentPasswordSelectCourseView.as_view(),
        name='change_student_password_select_course'),
    re_path(r'^login/',
        vv.IndexView.as_view(),
        name='login'),
    re_path(r'^logout/',
        vv.logout_view,
        name='logout_index'),
    re_path(r'^perfil/',
        vv.PerfilView.as_view(),
        name='perfil'),
    path('teacher/students/<int:student_id>/',
        vv.VideoclasesStudentView.as_view(),
        name='videoclases_student'),
    re_path(r'^teacher/assign-group-form/',
        vv.AssignGroupFormView.as_view(),
        name='assign_group_form'),
    path('teacher/delete-student/<int:course_id>/<int:student_id>/',
        vv.DeleteStudentView.as_view(),
        name='borrar_student'),
    path('teacher/delete-course/<int:course_id>/',
        vv.DeleteCourseFormView.as_view(),
        name='delete_course'),
    re_path(r'^teacher/delete-homework/',
        vv.DeleteHomeworkFormView.as_view(),
        name='delete_course'),
    re_path(r'^teacher/new-course/',
        vv.NewCourseFormView.as_view(),
        name='new_course'),
    re_path(r'^teacher/new-homework/',
        vv.NewHomeworkView.as_view(),
        name='new_homework'),
    re_path(r'^teacher/new-homework-form/',
        vv.NewHomeworkFormView.as_view(),
        name='new_homework_form'),

    path('teacher/new-conceptual-test/create/',
        pq.ConceptualTestsView.as_view(),
        name='new_conceptual_test_create'),
    path('teacher/new-conceptual-test/',
        pq.PedagogicalQuestionCreateView.as_view(),
        name='new_conceptual_test'),
    re_path(r'^teacher/new-test-conceptual-form/',
        pq.ConceptualTestsFormView.as_view(),
        name='new_conceptual_test_form'),
    path('teacher/download-homeworks/<int:course_id>/',
        pq.download_homeworks,
        name='download_homeworks'),
    path('teacher/download-pedagogical-questions/<int:pk>/',
        pq.DownloadPedagogicalQuestionAsExcel.as_view(),
        name='download_pedagogical_questions'),
    path('teacher/download-pedagogical-questions-answers/<int:pk>/',
        pq.DownloadPedagogicalQuestionAnswersAsExcel.as_view(),
        name='download_pedagogical_questions_answers'),
    path('teacher/pedagogical-questions/<int:pk>/',
        pq.PedagogicalQuestionEditView.as_view(),
        name='pedagogical_questions'),

    path('teacher/homework-evaluations/<int:pk>/',
        hw.HomeworkEvaluationsView.as_view(),
        name='homework_evaluations'),
    path('teacher/homework-evaluations-teacher/<int:pk>/',
        hw.HomeworkEvaluationsTeacherView.as_view(),
        name='homework_evaluations_teacher'),
    path('teacher/course/<int:course_id>/',
        vv.CourseView.as_view(),
        name='course'),
    path('teacher/download-course/<int:course_id>/',
        vv.download_course,
        name='download_course'),
    path('teacher/download-groups-homework/<int:homework_id>/',
        vv.download_homework_groups,
        name='download_homework_groups'),
    path('teacher/edit-student/<int:course_id>/<int:student_id>/',
        vv.EditStudentFormView.as_view(),
        name='edit_student'),
    path('teacher/edit-course/<int:course_id>/',
        vv.EditCourseView.as_view(),
        name='edit_course'),
    re_path(r'^teacher/edit-group-form/',
        vv.EditGroupFormView.as_view(),
        name='edit_group_form'),
    path('teacher/edit-homework-form/<int:homework_id>/',
        vv.EditHomeworkView.as_view(),
        name='edit_homework_form'),
    re_path(r'^teacher/upload-score/',
        vv.UploadScoreFormView.as_view(),
        name='upload_score'),
    path('teacher/homework/<int:homework_id>/',
        vv.EditHomeworkView.as_view(),
        name='homework'),
    re_path(r'^teacher/videoclases-homework/(?P<homework_id>\d+)/',
        vv.VideoclasesHomeworkView.as_view(),
        name='videoclases_homework'),
    re_path(r'^teacher/',
        vv.TeacherView.as_view(),
        name='teacher'),
]
