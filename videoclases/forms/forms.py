#-*- coding: UTF-8 -*-

from django import forms
from django.utils import timezone

from videoclases.models.student import Student
from videoclases.models.course import Course
from videoclases.models.student_evaluations import StudentEvaluations
from videoclases.models.student_responses import StudentResponses
from videoclases.models.homework import Homework
from videoclases.models.video_clase import VideoClase


class AssignGroupForm(forms.Form):
    groups = forms.CharField(max_length=1000000000, required=True)
    homework = forms.IntegerField(min_value=1, required=True)


class DeleteCourseForm(forms.Form):
    course = forms.IntegerField(min_value=1, required=True)


class DeleteHomeworkForm(forms.Form):
    homework = forms.IntegerField(min_value=1, required=True)


class ChangePasswordForm(forms.Form):
    error_messages = {
        'email_required': 'Debes ingresar un correo.',
        'password_incorrect': 'Clave incorrecta.',
        'password_mismatch': 'Las contraseñas no coinciden.',
    }

    old_password = forms.CharField(label="Contraseña antigua",
                                   widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="Nueva contraseña",
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirmar nueva contraseña",
                                    widget=forms.PasswordInput)
    email = forms.EmailField(label="Ingresa tu correo",
                             required=False)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(ChangePasswordForm, self).__init__(*args, **kwargs)


    def in_students_group(self, user):
        if user:
            return user.groups.filter(name='Alumnos').exists()
        return False

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.in_students_group(self.user):
            if not email:
                raise forms.ValidationError(
                    self.error_messages['email_required'],
                    code='email_required',
                )
        return email

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def clean_old_password(self):
        """
        Validates that the old_password field is correct.
        """
        old_password = self.cleaned_data['old_password']
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        return old_password

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if self.in_students_group(self.user) and self.cleaned_data.get('email'):
            self.user.email = self.cleaned_data['email']
        if commit:
            self.user.save()
        return self.user


#
# ModelChoiceField to override label in form
#
class StudentChoiceField(forms.models.ModelChoiceField):
    
    def label_from_instance(self, obj):
        return obj.user.get_full_name()


class ChangeStudentPasswordForm(forms.Form):
    error_messages = {
        'invalid_choice': 'Debes seleccionar un alumno.',
        'password_mismatch': 'Las contraseñas no coinciden.',
    }
    student = StudentChoiceField(queryset=Student.objects.all(), error_messages=error_messages)
    new_password1 = forms.CharField(label="Nueva contraseña",
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirmar nueva contraseña",
                                    widget=forms.PasswordInput)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def save(self, commit=True):
        student_user = self.cleaned_data['student'].user
        student_user.set_password(self.cleaned_data['new_password1'])
        if commit:
            student_user.save()
        return student_user


class ChangeStudentPasswordSelectCursoForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all())


class NewCourseUploadFileForm(forms.Form):
    file = forms.FileField()
    name = forms.CharField(required=True)
    year = forms.IntegerField(min_value=2015, required=True)

    def __init__(self, *args, **kwargs):
        super(NewCourseUploadFileForm, self).__init__(*args, **kwargs)
        self.fields['year'].label = "Año"
        self.fields['name'].label = "Nombre de Curso"
        self.fields['file'].label = "Planilla"


class NewHomeworkForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ['video', 'title', 'description', 'course', 'revision',
                  'date_upload', 'date_evaluation','homework_to_evaluate']
        dateOptions = {
            'weekStart': 1,
            'todayHighlight': True,
            'startDate': timezone.now().strftime('%d-%m-%Y')
        }

    def clean(self):
        date_upload = self.cleaned_data.get('date_upload')
        date_evaluation = self.cleaned_data.get('date_evaluation')
        if date_evaluation < date_upload:
            msg = u'Fecha para evaluar debe ser posterior a Fecha para subir homework.'
            self._errors['date_evaluation'] = self.error_class([msg])


class EditStudentForm(forms.Form):
    first_name = forms.CharField(required=True, label='Nombres')
    last_name = forms.CharField(required=True, label='Apellidos')


class EditHomeworkForm(forms.ModelForm):

    class Meta:
        model = Homework
        fields = ['video', 'title', 'description', 'course', 'revision',
                  'date_upload', 'date_evaluation', 'homework_to_evaluate', 'scale']
        dateOptions = {
            'weekStart': 1,
            'todayHighlight': True,
            'startDate': timezone.now().strftime('%d-%m-%Y')
        }

    def clean(self):
        if self.cleaned_data.get('date_upload'):
            date_upload = self.cleaned_data.get('date_upload')
        else:
            date_upload = self.instance.date_upload
        if self.cleaned_data.get('date_evaluation'):
            date_evaluation = self.cleaned_data.get('date_evaluation')
        else:
            date_evaluation = self.instance.date_evaluation
        if date_evaluation < date_upload:
            msg = u'Fecha para evaluar debe ser posterior a Fecha para subir homework.'
            self._errors['date_evaluation'] = self.error_class([msg])

    def save(self, commit=True):
        instance = super(EditHomeworkForm, self).save(commit=False)
        if self.cleaned_data.get('video', None) is not None:
            instance.video = self.cleaned_data['video']
        if self.cleaned_data.get('video', None) == 'empty video':
            instance.video = u""
        if self.cleaned_data.get('homework_to_evaluate', None) == instance:
            instance.homework_to_evaluate = None

        if commit:
            instance.save()
        return instance


class SendVideoclaseForm(forms.ModelForm):

    class Meta:
        model = VideoClase
        fields = ['video', 'question', 'correct_alternative',
                  'alternative_2', 'alternative_3']


class StudentEvaluationsForm(forms.ModelForm):

    class Meta:
        model = StudentEvaluations
        fields = '__all__'
        exclude = ['author', 'criteria']


class StudentResponsesForm(forms.ModelForm):

    class Meta:
        model = StudentResponses
        fields = ['videoclase', 'answer']


class UploadScoreForm(forms.Form):
    student = forms.IntegerField(min_value=1, required=True)
    group = forms.IntegerField(min_value=1, required=True)
    nota = forms.FloatField(min_value=1, max_value=7, required=True)