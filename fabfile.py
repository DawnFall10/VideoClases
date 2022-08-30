from fabric.contrib import django as ddd
import django

ddd.project("project")
django.setup()

import getpass

from django.contrib.auth.models import User
from fabric.api import env, require, run, sudo, cd, local, get

from project.fabfile_secret import *

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
file_name = 'VideoClasses/project/settings_secret.py'
template_name = 'VideoClasses/project/settings_secret.py.template'


def _load_data(reboot=False):
    local('python3 manage.py makemigrations')
    local('python3 manage.py migrate')
    if reboot:
        fixtures = ['devgroups', 'devusers', 'devschool', 'devcourses', 'devstudents', 'devteachers',
                    'devhomeworks']
        for f in fixtures:
            local('python3 manage.py loaddata ' + f)


# fab devserver -> states that you will connect to devserver server
def devserver():
    env.hosts = [env.server_name]


# activates videoclases virtualenv in server
def virtualenv(command, use_sudo=False):
    if use_sudo:
        func = sudo
    else:
        func = run
    func('source %sbin/activate && %s' % (env.virtualenv_root, command))


# creates file in ~/
# usage: fab devserver test_connection
def test_connection():
    require('hosts', provided_by=[devserver])
    virtualenv('echo "It works!" > fabric_connection_works.txt')


# util for prompt confirmation
def _confirm():
    prompt = "Please confirm you want to sync the branch 'master' in the server 'buho'"
    prompt = '%s [%s/%s]: ' % (prompt, 'y', 'n')

    while True:
        ans = input(prompt)
        if not ans:
            print('Please answer Y or N.')
            continue
        if ans not in ['y', 'Y', 'n', 'N']:
            print('Please answer Y or N.')
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False


# updates dev server project from git repository
def update():
    require('hosts', provided_by=[devserver])
    with cd(env.repo_root):
        run('git pull origin master')


# installs requirements in server
def install_requirements():
    require('hosts', provided_by=[devserver])
    virtualenv('pip3 install -q -r %(requirements_file)s' % env)


# aux function for calling manage.py functions
def manage_py(command, use_sudo=False):
    require('hosts', provided_by=[devserver])
    with cd(env.manage_dir):
        virtualenv('python manage.py %s' % command, use_sudo)


# syncs db in server
def makemigrations():
    require('hosts', provided_by=[devserver])
    manage_py('makemigrations')


# south migrate for db
def migrate():
    require('hosts', provided_by=[devserver])
    manage_py('migrate')


# collects static files
def collectstatic():
    require('hosts', provided_by=[devserver])
    manage_py('collectstatic --noinput')


# restarts apache in server
def reload():
    require('hosts', provided_by=[devserver])
    sudo('service apache2 restart')


# deploy on development server
def deploy():
    require('hosts', provided_by=[devserver])
    if _confirm():
        update()
        install_requirements()
        makemigrations()
        migrate()
        collectstatic()
        reload()
    else:
        print('Deploy cancelado')


# sync and migrate local db and start server
def restart(reboot=False):
    _load_data(reboot)
    local('python manage.py runserver 0.0.0.0:8000')


# reset local db and start server
def reboot():
    try:
        local('rm db.sqlite3')
    except:
        pass
    restart(True)


def _create_teacher():
    print('---------------------------------------')
    print('Now you will be asked for the necessary data to create a Professor.')

    from videoclases.models.course import Course
    from videoclases.models.teacher import Teacher
    from videoclases.models.school import School

    username = input('Insert username: ')
    user, created = User.objects.get_or_create(username=username)
    if created:
        password = getpass.getpass('Insert password: ')
        password2 = getpass.getpass('Confirm password: ')
        while password != password2:
            print('Passwords were not equal.')
            password = getpass.getpass('Insert password again: ')
            password2 = getpass.getpass('Confirm password: ')
        first_name = input('Insert first name: ')
        last_name = input('Insert last name: ')

        user.password = password
        user.first_name = first_name
        user.last_name = last_name
        user.save()

    school_name = input('Insert school name: ')
    school, created = School.objects.get_or_create(name=school_name)
    if created:
        school.save()
    course = input('Insert course name: ')
    cu, created = Course.objects.get_or_create(name=course, school=school)
    if created:
        cu.save()
    p, created = Teacher.objects.get_or_create(user=user, school=school)
    p.courses.add(cu)
    p.save()


def install():
    local('cp ' + os.path.join(BASE_DIR, template_name) + ' ' + os.path.join(BASE_DIR, file_name))
    _load_data()
    local('python3 manage.py collectstatic --noinput -l')
    local('python3 manage.py test')
    local('python3 manage.py loaddata devgroups')
    _create_teacher()
    local('python manage.py runserver 0.0.0.0:8000')


def install_with_data():
    local('cp ' + os.path.join(BASE_DIR, template_name) + ' ' + os.path.join(BASE_DIR, file_name))
    _load_data(True)
    local('python manage.py collectstatic --noinput -l')
    local('python manage.py test')
    local('python manage.py runserver 0.0.0.0:8000')
