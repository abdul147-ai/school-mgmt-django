from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('logout', views.logout_view, name='logout'),
    path('', views.login_view, name='login.html'),
    path('login/', views.login_view, name='login_view'),

    path('admin_signup/', views.admin_signup, name='admin_signup'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('students/', views.student_view, name='students'),
    path('student/details/<int:id>', views.student_details, name='student_details'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/edit/<int:id>/', views.edit_student, name='edit_student'),
    path('students/delete/<int:id>/', views.delete_student, name='delete_student'),

    path('teachers/', views.teacher_view, name='teachers'),
    path('teacher/details/<int:id>/', views.teacher_details, name='teacher_details'),
    path('teacher/add/', views.add_teacher, name='add_teacher'),
    path('teacher/edit/<int:id>/', views.edit_teacher, name='edit_teacher'),
    path('teacher/delete/<int:id>/', views.delete_teacher, name='delete_teacher'),

    path('departments/', views.department_list, name='department_list'),
    path('department/add/', views.add_department, name='add_department'),
    path('department/edit/<int:id>/', views.edit_department, name='edit_department'),
    path('department/delete/<int:id>/', views.delete_department, name='delete_department'),

    path('attendance/teachers/', views.admin_teacher_attendance, name='admin_teacher_attendance'),
    path('attendance/teachers/view/', views.admin_teacher_attendance_view, name='admin_teacher_attendance_view'),

    path('timetable/create/class/<int:class_id>/', views.timetable_create, name='bulk_timetable_create'),
    path('timetable/class/', views.class_wise_timetable, name='class_wise_timetable'),
    path('timetable/class/<int:class_id>/', views.class_wise_timetable, name='class_wise_timetable_detail'),
    path('timetable/teacher/', views.teacher_wise_timetable, name='teacher_wise_timetable'),
    path('timetable/teacher/<int:teacher_id>/', views.teacher_wise_timetable, name='teacher_wise_timetable_detail'),
    path('timetable/dashboard/', views.timetable_dashboard, name='timetable_dashboard'),

    #admin account urls
    path('accounts/', views.admin_account_dashboard, name='admin_account_dashboard'),
    path('salaries/', views.admin_teacher_salaries, name='admin_teacher_salaries'),
    path('salaries/payment/<int:account_id>/', views.admin_record_salary_payment,name='admin_record_salary_payment'),
    path('salaries/mark-paid/<int:account_id>/', views.admin_mark_salary_paid, name='admin_mark_salary_paid'),
    path('salaries/mark-pending/<int:account_id>/', views.admin_mark_salary_pending,name='admin_mark_salary_pending'),
    path('salaries/slip/<int:account_id>/', views.admin_generate_payment_slip,name='admin_generate_payment_slip'),
    path('salaries/history/<int:teacher_id>/', views.admin_salary_history, name='admin_salary_history'),
    path('salaries/generate-all/', views.admin_generate_all_salaries, name='admin_generate_all_salaries'),

    # Fee Management URLs
    path('fee-classes/', views.admin_fee_class_list, name='admin_fee_class_list'),
    path('class-fees/<int:class_id>/', views.admin_class_student_fees, name='admin_class_student_fees'),
    path('record-fee-payment/<int:student_id>/', views.record_fee_payment, name='record_fee_payment'),
    path('fee-receipt/<int:account_id>/', views.generate_fee_receipt, name='generate_fee_receipt'),
    path('student-fee-history/<int:student_id>/', views.student_fee_history, name='student_fee_history'),

    path('expenses/record/', views.record_expense, name='record_expense'),
    path('expenses/list/', views.expense_list, name='expense_list'),
    path('expenses/delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),

    path('financial-report/', views.financial_report, name='financial_report'),
]

    # teachers urls
urlpatterns +=[
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/students/add/', views.teacher_add_student, name='teacher_add_student'),
    path('teacher/students/<int:id>/', views.teacher_student_details, name='teacher_student_details'),
    path('teacher/students/<int:id>/edit/', views.teacher_edit_student, name='teacher_edit_student'),
    path('teacher/students/<int:id>/delete/', views.teacher_delete_student, name='teacher_delete_student'),
    path('teacher/department/', views.teacher_department_view, name='teacher_department'),

    path('subjects/', views.subject_list, name='subject_list'),
    path('subject/add/', views.add_subject, name='add_subject'),
    path('subject/edit/<int:id>/', views.edit_subject, name='edit_subject'),
    path('subject/delete/<int:id>/', views.delete_subject, name='delete_subject'),

    path('class/', views.class_list, name='class_list'),
    path('class/add/', views.add_class, name='add_class'),
    path('class/edit/<int:id>/', views.edit_class, name='edit_class'),
    path('class/delete/<int:id>/', views.delete_class, name='delete_class'),
    path('class/details/<int:id>/', views.class_details, name='class_details'),

    # attendance
    path('teacher/attendance/students/mark/', views.teacher_mark_student_attendance,name='teacher_mark_student_attendance'),
    path('teacher/attendance/students/save/', views.teacher_save_student_attendance,name='teacher_save_student_attendance'),
    path('teacher/attendance/students/view/', views.teacher_student_attendance_view,name='teacher_student_attendance_view'),
    path('teacher/department/attendance/', views.hod_department_attendance, name='hod_department_attendance'),

    path('teacher/timetable/', views.teacher_timetable_view, name='teacher_timetable'),
    path('teacher/student-fees/', views.teacher_student_fees_view, name='teacher_student_fees'),

    # Assignment URLs
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('teacher/assignments/create/', views.teacher_create_assignment, name='teacher_create_assignment'),
    path('teacher/assignments/<int:assignment_id>/', views.teacher_assignment_detail, name='teacher_assignment_detail'),
    path('teacher/assignments/<int:assignment_id>/delete/', views.teacher_delete_assignment,name='teacher_delete_assignment'),

    # Syllabus URLs
    path('teacher/syllabus/', views.teacher_syllabus, name='teacher_syllabus'),
    path('teacher/syllabus/add/', views.teacher_add_syllabus_topic, name='teacher_add_syllabus_topic'),
    path('teacher/syllabus/<int:topic_id>/edit/', views.teacher_edit_syllabus_topic,name='teacher_edit_syllabus_topic'),
    path('teacher/syllabus/<int:topic_id>/delete/', views.teacher_delete_syllabus_topic,name='teacher_delete_syllabus_topic'),
    path('teacher/syllabus/<int:topic_id>/toggle-complete/', views.teacher_mark_topic_complete,name='teacher_mark_topic_complete'),

]


urlpatterns +=[
    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/attendance/', views.student_attendance_view, name='student_attendance'),
    path('student/timetable/', views.student_timetable_view, name='student_timetable'),
    path('student/fee-summary/', views.student_fee_summary, name='student_fee_summary'),

    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/assignments/<int:assignment_id>/', views.student_assignment_detail, name='student_assignment_detail'),
    path('student/assignments/<int:assignment_id>/view/', views.student_view_submission,name='student_view_submission'),
    path('student/syllabus/', views.student_syllabus, name='student_syllabus'),



]