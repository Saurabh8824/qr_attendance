from django.urls import path
from . import views

urlpatterns = [
    # Home & Dashboard
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),

    # Students
    path("student/signup/", views.student_signup, name="student_signup"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/timetable/", views.student_timetable, name="student_timetable"),
    path("student/profile/", views.student_profile, name="student_profile"),
    path("students/", views.student_list, name="student_list"),
    path("students/add/", views.add_student, name="add_student"),
    path("scan/", views.student_scan, name="student_scan"),
    path("alerts/", views.student_alerts, name="student_alerts"),

    # Subjects
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/add/", views.add_subject, name="add_subject"),

    # QR Generate + Scan
    path("qr/generate/", views.generate_qr, name="qr_generate"),
    path("qr/scan/qr/", views.scan_qr, name="scan_qr"),
    path("qr/scan/form/<str:token>/", views.scan_form, name="scan_form"),

    path("qr/generate/", views.generate_qr, name="attendance_live"),

    # Attendance
    path("form/<str:token>/", views.attendance_form, name="attendance_form"),
    path("attendance/form/<str:token>/", views.attendance_form, name="attendance_form"),
    path("attendance/dashboard/", views.attendance_dashboard, name="attendance_dashboard"),
    path("attendance/faculty/", views.attendance_faculty, name="attendance_faculty"),
    path("attendance/stu/", views.attendance_stu, name="attendance_stu"),
    path("attendance/report/", views.report, name="report"),
    path("api/session/<int:session_id>/attendance/", views.session_attendance_api, name="session_attendance_api"),
    path("attendance/mark/", views.mark_attendance, name="mark_attendance"),

    # Ajax endpoint
    path("ajax/get-subjects/", views.ajax_get_subjects, name="ajax_get_subjects"),
    path("student/timetable/ajax/", views.get_timetable_ajax, name="timetable_ajax"),
    path('api/live-feed/', views.live_attendance_feed, name='live_attendance_feed'),
    path('api/active-sessions/', views.live_active_sessions, name='live_active_sessions')

    # Success & Error
    path("success/", views.success, name="success"),
    path("error/", views.error, name="error"),
    
    #Timetable
    
    path("timetable/add/", views.add_timetable, name="add_timetable"),
    path("timetable/view/", views.view_timetable, name="view_timetable"),

    #Teacher
    path("teacher/alert/create/", views.create_alert, name="create_alert"),
    path("teacher/alerts/", views.teacher_alerts, name="teacher_alerts"),
]




