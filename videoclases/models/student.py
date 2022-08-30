from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from videoclases.models.course import Course


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course, related_name='students')
    changed_password = models.BooleanField(default=False)

    def course_actual(self):
        course_qs = self.courses.filter(year=timezone.now().year)
        return course_qs[0] if course_qs.exists() & course_qs.count() > 0 else None

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return self.user.get_full_name()

    def display_courses(self):
        return ', '.join([
            u'{0} - {1}'.format(course.name, course.year)
            for course in self.courses.all()])

    display_courses.short_description = 'Courses'
    get_full_name.short_description = 'Name'
    get_full_name.admin_order_field = 'user__last_name'
    display_courses.admin_order_field = 'courses'

    class Meta:
        verbose_name = 'Estudiante'
