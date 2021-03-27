from django.urls import path

from .views import*

urlpatterns = [
    path('', redirect_to_workbench, name='empty_url'),
    path('workbench/<str:pagetype>', user_workbench, name='user_workbench_url'),
    path('task', tasks_list, name='tasks_list_url'),
    path('task/create/', task_create, name='task_create_url'),
    path('task/<str:id>', task_detail_or_edit, name='task_detail_url'),
    path('task-delete/<str:id>', task_del, name='task_del_url'),
    path('task-delete-many', task_del_many, name='task_del_many_url'),

    path('user', users_list, name='users_list_url'),
    path('user/<str:id>', user_detail_or_edit, name='user_detail_url'),
    path('login', login_page, name='login_page_url'),
    path('logout', logout_user, name='logout_user_url'),
    path('register', register_page, name='register_page_url'),

    path('roles', users_roles_list, name='users_roles_url'),
    path('role/<str:id>', UserRoleDetail.as_view(), name='users_role_url'),

    path('messages', user_messages, name='user_messages_url'),
    path('messages-delete', delete_user_messages, name='delete_user_messages_url'),

    path('reminders', user_reminders, name='user_reminders_url'),

    path('department', departments_list, name='departments_url'),
    path('department/create', department_create, name='department_create_url'),
    path('department/delete/<str:id>', department_del, name='department_del_url'),
    path('department/edit/<str:id>', department_edit, name='department_edit_url'),
    path('department/<str:id>', department_detail, name='department_detail_url'),

    path('task_status', task_statuses_list, name='task_statuses_url'),
]
