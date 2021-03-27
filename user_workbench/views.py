from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import reverse
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.db import models

from .functions import*


TASKS_ON_PAGE_AMOUNT = 13
MESSAGES_ON_PAGE_AMOUNT = 30
@login_required(login_url='login_page_url')
def redirect_to_workbench(request):
    return redirect(reverse('user_workbench_url', kwargs={'pagetype':'all'}))


@login_required(login_url='login_page_url')
def user_workbench(request, pagetype):
    current_user = request.user.profile

    # Search parameters from GET dict
    search_by_status = request.GET.get('search_by_status', 'undn')
    search_by_responsible = request.GET.getlist('search_by_responsible')
    checkbox_deadline = request.GET.get('checkbox_deadline', False)
    bottom_number = request.GET.get('bottom_number', 0)
    bottom_number_type = request.GET.get('bottom_number_type', 'months')
    top_number = request.GET.get('top_number', 0)
    top_number_type = request.GET.get('top_number_type', 'months')
    bottom_date = request.GET.get('bottom_date', 0)
    top_date = request.GET.get('top_date', 0)
    search_by_name = request.GET.get('search_by_name', '')
    search_by_justification = request.GET.get('search_by_justification', '')
    search_by_author = request.GET.get('search_by_author', '')

    # Ordering parameters from GET dict
    ordering_by = request.GET.get('ordering_by', '')
    ordering_type = request.GET.get('ordering_type', '')

    if pagetype == 'ct':
        tasks = request.user.profile.created_tasks.all()
    elif pagetype == 'at':
        tasks = request.user.profile.assigned_tasks.all()
    elif pagetype == 'all':
        tasks = Task.objects.all()

    if search_by_status == "undn":
        tasks = tasks.filter(status__in=['ns', 'ip', 'hs'])

    elif search_by_status != "all":
        tasks = tasks.filter(status__exact=search_by_status)

    if search_by_responsible:
        tasks = tasks.filter(responsible_users__in=search_by_responsible)

    if not checkbox_deadline:
        if bottom_number:
            bottom_date = calc_deadline(dt.datetime.now(), {bottom_number_type: bottom_number})
        if top_number:
            top_date = calc_deadline(dt.datetime.now(), {top_number_type: top_number})

    if bottom_date:
        tasks = tasks.filter(deadline__gt=bottom_date)
    if top_date:
        tasks = tasks.filter(deadline__lt=top_date)

    if search_by_name:
        tasks = tasks.filter(name__icontains=search_by_name)

    if search_by_justification:
        tasks = tasks.filter(name__icontains=search_by_justification)

    if search_by_author:
        tasks = tasks.filter(Q(author__name__icontains=search_by_author) \
                        | Q(author__second_name__icontains=search_by_author) \
                        | Q(author__middle_name__icontains=search_by_author))

    if ordering_by == 'status':
        CASE_SQL = '(case when status="nw" then 0 when status="cn" then 1 when status="ns" then 2 when status="ip" then 3 when status="hs" then 4 when status="dn" then 5 when status="ch" then 6  end)'
        if ordering_type == 'ascending':

            tasks = tasks.extra(select={'task_order': CASE_SQL}, order_by=['task_order'])
        elif ordering_type == 'descending':
            tasks = tasks.extra(select={'task_order': CASE_SQL}, order_by=['-task_order'])

    elif ordering_by == 'name':
        if ordering_type == 'ascending':
            tasks = tasks.order_by('name')
        elif ordering_type == 'descending':
            tasks = tasks.order_by('-name')

    elif ordering_by == 'author':
        if ordering_type == 'ascending':
            tasks = tasks.order_by('author')
        elif ordering_type == 'descending':
            tasks = tasks.order_by('-author')

    elif ordering_by == 'deadline':
        if ordering_type == 'ascending':
            tasks = tasks.order_by('deadline')
        elif ordering_type == 'descending':
            tasks = tasks.order_by('-deadline')

    elif ordering_by == 'creation_datetime':
        if ordering_type == 'ascending':
            tasks = tasks.order_by('creation_datetime')
        elif ordering_type == 'descending':
            tasks = tasks.order_by('-creation_datetime')

    elif ordering_by == 'closure_datetime':
        if ordering_type == 'ascending':
            tasks = tasks.order_by('closure_datetime')
        elif ordering_type == 'descending':
            tasks = tasks.order_by('-closure_datetime')

    paginator = Paginator(tasks, TASKS_ON_PAGE_AMOUNT)
    page_number = request.GET.get('page', request.GET.get('page', 1))
    page = paginator.get_page(page_number)
    is_paginated = page.has_other_pages()

    context={'current_user': current_user,
            'page': page,
            'pagetype': pagetype,
            'users': UserProfile.objects.all(),
            'is_paginated': is_paginated,}

    return render(request,
        'user_workbench/workbench.html',
        context=context)


@login_required(login_url='login_page_url')
def tasks_list(request):
    tasks = Task.objects.all()
    context={'tasks': tasks}
    return render(request,
        'user_workbench/tasks_list.html',
        context=context)


@login_required(login_url='login_page_url')
def task_detail_or_edit(request, id):
    current_user = request.user.profile
    task = get_object_or_404(Task, id=id)
    responsible_users = task.responsible_users.all()
    sub_tasks = task.sub_tasks.all()
    FormClass = define_mf_for_task(task, request.user.profile)
    template_contains = define_template_containing(task, request.user.profile)
    if request.method == 'POST':
        old_data = model_to_dict(task)
        form = FormClass(request.POST, instance=task)
        if 'deadline' in form.fields:
            deadline_limit = task.super_task.deadline if task.super_task else dt.datetime.max
            validate_deadline = deadline_validator_gen(deadline_limit)
            form.fields['deadline'].validators.append(validate_deadline)
        if form.is_valid(): # is_valid also updates task instance with new attributes!
            if has_changed(task, 'status'): # So we can check it before saving instance in DB:
                task.set_new_status()
            task = form.save(commit=True)
            #make_messages_about_changes(old_data, model_to_dict(task), current_user, task)
            return redirect(task)
        else:
            messages.warning(request, form.errors)

    form = FormClass(instance=task)
    context={'current_user': current_user,
        'form': form,
        'task': task,
        'responsible_users': responsible_users,
        'sub_tasks': sub_tasks,
        'template_contains': template_contains,
        'COLOR_DIS': COLORS['disabled'],
        'COLOR_EN': COLORS['enabled'],}
    return render(request,
            'user_workbench/task_detail.html',
            context=context)


@login_required(login_url='login_page_url')
def task_create(request):
    current_user = request.user.profile
    FormClass = create_task_form(('name', 'body', 'deadline', 'responsible_users', 'justification', 'comment'), userprofile)
    id = request.GET.get('id', '0')
    super_task = get_object_or_404(Task, id=id) if id != '0' else None


    if request.method == 'POST':
        id = request.POST.get('id', '0')
        super_task = get_object_or_404(Task, id=id) if id != '0' else None
        deadline_limit = super_task.deadline if super_task else dt.datetime.max
        bound_f = FormClass(request.POST)
        validate_deadline = deadline_validator_gen(deadline_limit)
        bound_f.fields['deadline'].validators.append(validate_deadline)
        if bound_f.is_valid():
            task = bound_f.save(commit=False)
            if task_create_permission(super_task, userprofile):
                task.author = current_user
                if super_task:
                    task.super_task = super_task
                    super_task.status = Task.HAS_SUBTASK
                    super_task.save()
                task.save()
                bound_f.save_m2m()
                #make_messages_about_creation(task)
                return redirect(task)

            else:
                messages.warning(request, 'Задача не может быть создана: нет прав.')
        else:
            messages.warning(request, bound_f.errors)

        context = {'current_user': request.user.profile,
                    'form': bound_f,
                    'userprofile': current_user,
                    'super_task': super_task,}

        return render(request,
                'user_workbench/task_create.html',
                context=context)

    if request.method == 'GET':
        f = FormClass()
        context = {'current_user': current_user,
                    'form': f,
                    'userprofile': current_user,
                    'super_task': super_task,}
        return render(request,
            'user_workbench/task_create.html',
            context=context)


@login_required(login_url='login_page_url')
def task_del(request, id):
    task = get_object_or_404(Task, id=id)
    task.delete()
    return redirect(reverse('user_workbench_url', kwargs={'pagetype': 'all'}))


@login_required(login_url='login_page_url')
def task_del_many(request):
    tasks = Task.objects.filter(closure_datetime__isnull=False)
    age = request.POST.get('age')
    tasks = tasks.filter(deadline__lt=age)
    tasks = tasks.filter(super_task__isnull=True)
    tasks.delete()
    return redirect(reverse('user_workbench_url', kwargs={'pagetype': 'all'}))


@login_required(login_url='login_page_url')
def task_statuses_list(request):
    statuses = TaskStatus.objects.all()
    context={'statuses': statuses}
    return render(request,
        'user_workbench/task_statuses_list.html',
        context=context)


@login_required(login_url='login_page_url')
def users_list(request):
    context={'current_user': request.user.profile,
            'profiles': UserProfile.objects.all()}
    return render(request,
        'user_workbench/users_list.html',
        context=context)


def register_page(request):
    if request.user.is_authenticated:
        return redirect(reverse('user_workbench_url', kwargs={'pagetype': 'all'}))

    if request.method == 'POST':
        b_form = UserForm(request.POST)
        b_form_2 = UserProfileForm(request.POST)

        if b_form.is_valid() and b_form_2.is_valid():
            user = b_form.save()
            profile = UserProfile.objects.create(user=user,
                                name=b_form_2.cleaned_data.get('name'),
                                second_name=b_form_2.cleaned_data.get('second_name'),
                                middle_name=b_form_2.cleaned_data.get('middle_name'))
            profile.save()
            return redirect(reverse('login_page_url'))

        return render(request,
                'user_workbench/register.html',
                context={'form':b_form, 'form_2':b_form_2})

    # If method is not POST, just render register page with empty form
    form = UserForm()
    form_2 = UserProfileForm()

    context={'form':form, 'form_2':form_2}
    return render(request,
        'user_workbench/register.html',
        context=context)


def login_page(request):
    if request.user.is_authenticated:
        return redirect(reverse('user_workbench_url', kwargs={'pagetype': 'at'}))

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(reverse('user_workbench_url', kwargs={'pagetype': 'at'}))

        messages.info(request, 'Не правильный пароль ИЛИ имя пользователя.')

    context={}
    return render(request,
        'user_workbench/login.html',
        context=context)


@login_required(login_url='login_page_url')
def logout_user(request):
    logout(request)
    return redirect(reverse('login_page_url'))


@login_required(login_url='login_page_url')
def user_detail_or_edit(request, id):
    profile = get_object_or_404(UserProfile, id=id)
    username = profile.user.username
    department = profile.department
    slave_department = None
    if hasattr(profile, 'slave_department'):
        slave_department = profile.slave_department
    edit_permition = False
    form = None

    if request.user.profile == profile or request.user.is_staff:
        form = UserProfileForm(instance=profile)
        edit_permition = True

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect(profile)

    return render(request,
        'user_workbench/user_detail.html',
        context={'current_user': request.user.profile,
                'profile': profile,
                'edit_permition': edit_permition,
                'form': form,
                'department': department,
                'slave_department': slave_department,})


@login_required(login_url='login_page_url')
def users_roles_list(request):
    roles = UserRole.objects.all()
    return render(request,
        'user_workbench/users_roles_list.html',
        context={'roles': roles})


class UserRoleDetail(ObjectDetailMixin, View):
    model = UserRole
    template = 'user_workbench/user_role_detail.html'


@login_required(login_url='login_page_url')
def user_messages(request):
    current_user = request.user.profile
    if current_user.user.is_staff:
        messages = InfoMessage.objects.all()
    else:
        messages = current_user.received_messages.all()

    paginator = Paginator(messages, MESSAGES_ON_PAGE_AMOUNT)
    page_number = request.GET.get('page', request.GET.get('page', 1))
    page = paginator.get_page(page_number)
    is_paginated = page.has_other_pages()

    return render(request,
        'user_workbench/messages_list.html',
        context={'current_user': current_user,
                    'page': page,
                    'is_paginated': is_paginated})


@login_required(login_url='login_page_url')
def delete_user_messages(request):
    current_user = request.user.profile
    if current_user.user.is_staff:
        messages = InfoMessage.objects.all()
    else:
        messages = current_user.received_messages.all()
    if messages.exists():
        messages.delete()
    return redirect(reverse('user_messages_url'))


@login_required(login_url='login_page_url')
def user_reminders(request):
    current_user = request.user.profile
    now = dt.datetime.now()
    oneday = now + dt.timedelta(days=1)
    twodays = oneday + dt.timedelta(days=2)
    week = oneday + dt.timedelta(days=7)
    thirtydays = oneday + dt.timedelta(days=30)
    sixtydays = oneday + dt.timedelta(days=60)
    user_tasks = current_user.assigned_tasks
    unclosed_tasks = user_tasks.filter(closure_datetime__isnull=True)
    less_than_day_tasks = unclosed_tasks.filter(deadline__gt=now).filter(deadline__lt=oneday)
    less_than_twodays_tasks = unclosed_tasks.filter(deadline__gt=oneday).filter(deadline__lt=twodays)
    less_than_week_tasks = unclosed_tasks.filter(deadline__gt=twodays).filter(deadline__lt=week)
    less_than_thirtydays_tasks = unclosed_tasks.filter(deadline__gt=week).filter(deadline__lt=thirtydays)
    less_than_sixtydays_tasks = unclosed_tasks.filter(deadline__gt=thirtydays).filter(deadline__lt=sixtydays)
    overdue_tasks = unclosed_tasks.filter(deadline__lt=now)

    context={'current_user': current_user,
                'less_than_day_tasks': less_than_day_tasks,
                'less_than_twodays_tasks': less_than_twodays_tasks,
                'less_than_week_tasks': less_than_week_tasks,
                'less_than_thirtydays_tasks': less_than_thirtydays_tasks,
                'less_than_sixtydays_tasks': less_than_sixtydays_tasks,
                'overdue_tasks': overdue_tasks,}
    return render(request,
        'user_workbench/reminders.html',
        context=context)



@login_required(login_url='login_page_url')
def departments_list(request):
    current_user = request.user.profile
    if current_user.user.is_staff or current_user.chief:
        departments = Department.objects.all()
        return render(request,
            'user_workbench/departments_list.html',
            context={'current_user': current_user,
                    'departments': departments})
    else:
        return redirect(reverse('user_workbench_url', kwargs={'pagetype': 'at'}))


@login_required(login_url='login_page_url')
def department_detail(request, id):
    if current_user.user.is_staff or current_user.chief:
        department = get_object_or_404(Department, id=id)
        workers = department.workers.all()
        sub_departments = department.sub_departments.all()
        return render(request,
            'user_workbench/department_detail.html',
            context={'current_user': request.user.profile,
                    'department': department,
                    'workers': workers,
                    'sub_departments': sub_departments})
    else:
        return redirect(reverse('user_workbench_url', kwargs={'pagetype': 'at'}))


@login_required(login_url='login_page_url')
def department_create(request):
    current_user = request.user.profile
    if current_user.user.is_staff or current_user.chief:
        if request.method == 'POST':
            b_form = DepartmentForm(request.POST)
            if b_form.is_valid():
                department = b_form.save()
                department.workers.set(b_form.cleaned_data['workers'])
                department.save()
                return redirect(department)
            return render(request,
                    'user_workbench/department_create.html',
                    context={'current_user': current_user,
                            'form':b_form, })

        form = DepartmentForm()
        context={'current_user': current_user,
                'form':form}
        return render(request,
            'user_workbench/department_create.html',
            context=context)
    else:
        return redirect(reverse('user_workbench_url', kwargs={'pagetype': 'at'}))


@login_required(login_url='login_page_url')
def department_edit(request, id):
    current_user = request.user.profile
    department = get_object_or_404(Department, id=id)
    sub_departments = department.sub_departments.all()


    # ! Fixme !
    # Not enough autorization checkers. Need to expand on all options
    #

    if current_user != department.chief and not current_user.user.is_staff and not current_user.chief:
        return redirect(department)


    if request.method == 'POST':
        b_form = DepartmentForm(request.POST, instance=department)
        if b_form.is_valid():
            department = b_form.save()
            department.workers.set(b_form.cleaned_data['workers'])
            department.save()
            return redirect(department)

    form = DepartmentForm(instance=department)
    context={'current_user': current_user,
                'form': form,
                'department': department,
                'sub_departments': sub_departments}
    return render(request,
        'user_workbench/department_edit.html',
        context=context)


@login_required(login_url='login_page_url')
def department_del(request, id):
    if current_user != department.chief and not current_user.user.is_staff and not current_user.chief:
        return redirect(department)
    department = get_object_or_404(Department, id=id)
    department.delete()
    return redirect(reverse('departments_url'))
