from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from datetime import timedelta, datetime
import qrcode, base64, io, uuid
import socket
import csv
from .models import Student, Subject, QRSession, Attendance, Branch, TimeTable, Alert, UserProfile
from django.utils.timezone import now, localdate
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .forms import StudentForm, SubjectForm
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from .decorators import teacher_required, student_required
from django.views.decorators.cache import never_cache



def get_user_role(user):
    return user.userprofile.role
    

# 🏠 Home Page
@never_cache
@login_required
@teacher_required
def home(request):
    return render(request, "qr_app/home.html")



@login_required
@student_required
def student_dashboard(request):
    return render(request, "qr_app/student_dashboard.html")


def student_signup(request):

    from django.contrib.auth.models import User
    from django.contrib.auth import login
    from django.contrib import messages
    from django.db import IntegrityError

    from .models import Student, Subject, Branch

    branches = Branch.objects.all()

    if request.method == "POST":

        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        enrollment = request.POST.get("enrollment")
        roll = request.POST.get("roll")
        semester = request.POST.get("semester")
        branch_id = request.POST.get("branch")

        # ✅ password check
        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("student_signup")

        # ✅ username duplicate check
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("student_signup")

        # ✅ enrollment duplicate check
        if enrollment:
            if Student.objects.filter(enrollment_no=enrollment).exists():
                messages.error(request, "Enrollment number already exists")
                return redirect("student_signup")

        # ✅ roll + sem + branch duplicate check
        if Student.objects.filter(
            roll_no=roll,
            semester=semester,
            branch_id=branch_id
        ).exists():

            messages.error(
                request,
                "Student with this Roll Number already exists in this Branch and Semester."
            )

            return redirect("student_signup")

        try:

            # ✅ create user
            user = User.objects.create_user(
                username=username,
                password=password1
            )
            
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "role": "student"
                }
            )

            # ✅ create student
            student = Student.objects.create(
                user=user,
                enrollment_no=enrollment,
                roll_no=roll,
                name=request.POST.get("name"),
                father_name=request.POST.get("father"),
                mother_name=request.POST.get("mother"),
                dob=request.POST.get("dob"),
                year=request.POST.get("year"),
                semester=semester,
                branch_id=branch_id,
                email=request.POST.get("email"),
                mobile=request.POST.get("mobile"),
            )

            # ✅ auto subject assign
            subjects = Subject.objects.filter(
                branch=student.branch,
                semester=student.semester
            )

            student.subjects.set(subjects)

            # ✅ login
            login(request, user)

            messages.success(request, "Registration Successful")

            return redirect("student_dashboard")

        except IntegrityError:

            messages.error(
                request,
                "Duplicate student data found."
            )

            return redirect("student_signup")

        except Exception as e:

            messages.error(
                request,
                f"Error: {str(e)}"
            )

            return redirect("student_signup")

    return render(request, "qr_app/student_signup.html", {
        "branches": branches
    })



@login_required
@student_required
def student_dashboard(request):

    if request.user.userprofile.role != "student":
        return redirect("home")

    try:
        student = Student.objects.get(user=request.user)

    except Student.DoesNotExist:
        return redirect("student_signup")

    subjects = student.subjects.all()

    today = datetime.now().strftime("%a")

    today_timetable = TimeTable.objects.filter(
        branch=student.branch,
        semester=student.semester,
        day=today
    )

    data = []

    total_present = 0
    total_classes = 0

    for subject in subjects:

        total = QRSession.objects.filter(
            subject=subject
        ).count()

        present = Attendance.objects.filter(
            student=student,
            qr_session__subject=subject
        ).count()
        # 🔥 attendance map
        attendance_map = {}
        sessions = QRSession.objects.filter(
            subject=subject
        ).order_by("created_at")
        for session in sessions:
            date_key = session.created_at.date()

            if date_key not in attendance_map:

                attendance_map[date_key] = {
                    "total": 0,
                    "present": 0,
                    "classes": []
                }

            attendance_map[date_key]["total"] += 1
            att = Attendance.objects.filter(
                student=student,
                qr_session=session
            ).exists()
            if att:
                attendance_map[date_key]["present"] += 1
            attendance_map[date_key]["classes"].append({
                "present": att,
                "status": (
                    "present"
                    if att
                    else "absent"
                ),
                "created_at": timezone.localtime(
                    session.created_at
                ).strftime("%I:%M %p"),
                "start_time": (
                    session.timetable.start_time.strftime("%I:%M %p")
                    if hasattr(session, "timetable")
                    and session.timetable
                    else ""
                ),
                "end_time": (
                    session.timetable.end_time.strftime("%I:%M %p")
                    if hasattr(session, "timetable")
                    and session.timetable
                    else ""
                )
            })

        # 🔥 convert to list
        attendance_records = []
        for dt, info in attendance_map.items():
            attendance_records.append({
                "date": dt,
                "present_count": info["present"],
                "total_count": info["total"],
                "status": (
                    "present"
                    if info["present"] == info["total"]
                    else "partial"
                    if info["present"] > 0
                    else "absent"
                ),
                "classes": info["classes"]

            })

        # 🔥 ADD TO DATA
        data.append({
            "id": subject.id,
            "name": subject.name,
            "code": subject.code,
            "present": present,
            "total": total,
            "attendance_records": attendance_records
        })

        total_present += present
        total_classes += total

    overall = total_present

    return render(request, "qr_app/student_dashboard.html", {
        "student": student,
        "subjects": data,
        "overall": overall,
        "total_classes": total_classes,
        "today_timetable": today_timetable

    })




# 📊 Dashboard (overall view)
import json as _json
from django.db.models import Count, Q
from django.utils import timezone
from datetime import time
import json
from django.db.models import Count
from django.utils import timezone
from datetime import time, timedelta
from .models import Student, Subject, QRSession, Attendance, Branch

@never_cache
@login_required
@teacher_required
def dashboard(request):
    today_start = timezone.make_aware(
        timezone.datetime.combine(timezone.localtime().date(), time.min)
    )
    branch_id = request.GET.get("branch")
    selected_sem = request.GET.get("semester")
    
    branches = Branch.objects.all()
    semester_choices = Student._meta.get_field("semester").choices

    # Base Queries initialization
    students_qs = Student.objects.all()
    subjects_qs = Subject.objects.all()
    attendance_today_qs = Attendance.objects.filter(timestamp__gte=today_start)
    reports_qs = QRSession.objects.all()
    recent_qs = Attendance.objects.select_related('student', 'qr_session__subject').order_by("-timestamp")

    # ── BRANCH AND SEMESTER FILTER SCHEME ──
    if branch_id and branch_id.strip() and branch_id != "None":
        students_qs = students_qs.filter(branch_id=branch_id)
        subjects_qs = subjects_qs.filter(branch_id=branch_id)
        attendance_today_qs = attendance_today_qs.filter(student__branch_id=branch_id)
        reports_qs = reports_qs.filter(subject__branch_id=branch_id)
        recent_qs = recent_qs.filter(student__branch_id=branch_id)

    if selected_sem and selected_sem.strip() and selected_sem != "None":
        students_qs = students_qs.filter(semester=selected_sem)
        if hasattr(Subject, 'semester'):
            subjects_qs = subjects_qs.filter(semester=selected_sem)

    # Filtered Total Registered Students Count
    students_count = students_qs.count()
    subjects_count = subjects_qs.count()
    reports_count = reports_qs.count()

    # ── NEW FIXED LOGIC FOR UNIQUE TODAY'S ATTENDANCE & SPLIT CHART ──
    # .values('student').distinct() का उपयोग करके हम सुनिश्चित कर रहे हैं कि 
    # एक छात्र चाहे जितनी भी क्लासेस में प्रेजेंट हो, आज के काउंट में वह 1 ही बार गिना जाएगा।
    todays_present_unique = attendance_today_qs.values('student').distinct().count()
    
    # अगर आज फ़िल्टर किए गए कुल छात्र (जैसे 40) हैं, तो एब्सेंट छात्र = कुल छात्र - यूनीक प्रेजेंट छात्र
    todays_absent_unique = max(0, students_count - todays_present_unique)

    # ── WEEKLY ATTENDANCE LINE CHART TREND ENGINE ──
    weekly_labels = []
    weekly_data = []
    today = timezone.localdate()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        weekly_labels.append(day.strftime("%a"))  # e.g., Mon, Tue
        day_count = Attendance.objects.filter(timestamp__date=day)
        
        if branch_id and branch_id.strip() and branch_id != "None":
            day_count = day_count.filter(student__branch_id=branch_id)
        if selected_sem and selected_sem.strip() and selected_sem != "None":
            day_count = day_count.filter(student__semester=selected_sem)
            
        # यहाँ भी दैनिक ट्रेंड को सही रखने के लिए यूनीक छात्रों को गिनना बेहतर है
        weekly_data.append(day_count.values('student').distinct().count())

    # ── ACCURATE DEFAULTERS PER-STUDENT TOTAL CLASSES LOGIC ──
    defaulters = []
    all_students = students_qs.prefetch_related('subjects')
    
    for student in all_students:
        total_student_classes = QRSession.objects.filter(subject__in=student.subjects.all()).count()
        present_count = Attendance.objects.filter(student=student).count()
        
        if total_student_classes > 0:
            percentage = round((present_count / total_student_classes) * 100)
        else:
            percentage = 0
            
        if percentage < 75:
            defaulters.append({
                'roll_no': student.roll_no,
                'name': student.name,
                'branch':     student.branch.name if student.branch else '—',
                'semester':   student.semester,
                'percentage': percentage,
                'present': present_count,
                'total': total_student_classes
            })
            
    defaulters = sorted(defaulters, key=lambda x: x['percentage'])[:5]

    # ── Bar chart breakdown stats for subjects (Scans vs Sessions) ──
    subject_stats = subjects_qs.annotate(
        total_scans=Count('qrsession__attendance'),
        total_sessions=Count('qrsession', distinct=True)
    ).values('name', 'total_scans', 'total_sessions')
    
    subject_names = [s['name'] for s in subject_stats]
    subject_scans = [s['total_scans'] for s in subject_stats]
    subject_sessions = [s['total_sessions'] for s in subject_stats]

    # Frontend Chart.js में Present/Absent Split भेजने के लिए JSON Array
    # index 0 पर Present और index 1 पर Absent का डेटा रहेगा
    donut_data = [todays_present_unique, todays_absent_unique]

    context = {
        "branches": branches,
        "semester_choices": semester_choices,
        "selected_branch": branch_id,
        "selected_semester": selected_sem,
        "students_count": students_count,
        "subjects_count": subjects_count,
        
        # कार्ड में दिखाने के लिए कुल यूनीक प्रेजेंट छात्र
        "todays_attendance_count": todays_present_unique, 
        "reports_count": reports_count,
        "attendance": recent_qs[:10],
        "defaulters": defaulters,
        
        # Chart JSON Data
        "weekly_labels_json": json.dumps(weekly_labels),
        "weekly_present_json": json.dumps(weekly_data),
        "subject_names_json": json.dumps(subject_names),
        "subject_scans_json": json.dumps(subject_scans),
        "subject_sessions_json": json.dumps(subject_sessions),
        
        # New Today Split Donut Data
        "donut_data_json": json.dumps(donut_data),
    }
    return render(request, "qr_app/dashboard.html", context)



@never_cache
@login_required
@teacher_required
def add_timetable(request):
    

    if request.method == "POST":
        TimeTable.objects.create(
            subject_id=request.POST.get("subject"),
            branch_id=request.POST.get("branch"),
            semester=request.POST.get("semester"),
            day=request.POST.get("day"),
            start_time=request.POST.get("start_time"),
            end_time=request.POST.get("end_time"),
            room=request.POST.get("room"),
            teacher_name=request.POST.get("teacher_name")
        )
        return redirect("add_timetable")

    subjects = Subject.objects.all()
    branches = Branch.objects.all()

    return render(request, "qr_app/add_timetable.html", {
        "subjects": subjects,
        "branches": branches
    })



@never_cache
@login_required
@teacher_required
def view_timetable(request):

    branches = Branch.objects.all()

    branch_id = request.GET.get("branch")
    semester = request.GET.get("semester")
    selected_day = request.GET.get("day", "Mon")   # ✅ correct

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    timetable = TimeTable.objects.all()

    if branch_id:
        timetable = timetable.filter(branch_id=branch_id)

    if semester:
        timetable = timetable.filter(semester=semester)

    # ✅ correct filter
    if selected_day:
        timetable = timetable.filter(day=selected_day)

    timetable = timetable.order_by("start_time")

    return render(request, "qr_app/timetable.html", {
        "timetable": timetable,
        "branches": branches,
        "selected_day": selected_day,
        "days": days
 })




@login_required
@student_required
def student_timetable(request):

    student = Student.objects.get(user=request.user)

    selected_day = request.GET.get("day", "Mon")

    timetable = TimeTable.objects.filter(
        branch=student.branch,
        semester=student.semester,
        day=selected_day
    ).order_by("start_time")

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    return render(request, "qr_app/student_timetable.html", {
        "timetable": timetable,
        "days": days,
        "selected_day": selected_day
    })


@login_required
def get_timetable_ajax(request):
    date = request.GET.get("date")

    selected_date = datetime.strptime(date, "%Y-%m-%d")
    day = selected_date.strftime("%a")  # Mon, Tue...

    student = Student.objects.get(user=request.user)

    timetable = TimeTable.objects.filter(
        branch=student.branch,
        semester=student.semester,
        day=day
    ).order_by("start_time")

    data = []

    for t in timetable:
        data.append({
            "subject": t.subject.name,
            "code": t.subject.code,
            "room": t.room,
            "teacher": t.teacher_name,
            "start": str(t.start_time),
            "end": str(t.end_time),
        })

    return JsonResponse({"timetable": data, "day": day})



@login_required
@student_required
def student_scan(request):
    student = Student.objects.get(user=request.user)

    return render(request, "qr_app/student_scan.html", {
        "student": student
    })



@login_required
@student_required
def student_alerts(request):

    student = Student.objects.get(user=request.user)

    alerts = Alert.objects.filter(
        Q(branch=student.branch) | Q(branch__isnull=True),
        Q(semester=student.semester) | Q(semester__isnull=True)
    ).order_by("-created_at")

    # counts
    total = alerts.count()
    high = alerts.filter(priority="high").count()
    today = alerts.filter(created_at__date=timezone.now().date()).count()

    return render(request, "qr_app/student_alerts.html", {
        "alerts": alerts,
        "total": total,
        "high": high,
        "today": today
    })



@login_required
@student_required
def student_profile(request):

    student = Student.objects.get(user=request.user)

    subjects = student.subjects.all()

    data = []
    total_present = 0
    total_classes = 0

    for subject in subjects:
        total = QRSession.objects.filter(subject=subject).count()

        present = Attendance.objects.filter(
            student=student,
            qr_session__subject=subject
        ).count()

        data.append({
            "name": subject.name,
            "code": subject.code,
            "present": present,
            "total": total
        })

        total_present += present
        total_classes += total

    # 🔥 NEW LOGIC
    overall = f"{total_present} / {total_classes}"

    # 🔥 STATUS LOGIC (count based)
    if total_classes == 0:
       status = "No Data"
    elif total_present < (total_classes * 0.5):
       status = "Low"
    else:
       status = "Good"

    return render(request, "qr_app/student_profile.html", {
        "student": student,
        "subjects": data,
        "overall": overall,
        "status": status
    })


@never_cache
@login_required
@teacher_required
def create_alert(request):

    branches = Branch.objects.all()

    if request.method == "POST":
        title = request.POST.get("title")   # 🔥 NEW
        message = request.POST.get("message")
        branch = request.POST.get("branch")
        semester = request.POST.get("semester")
        priority = request.POST.get("priority")

        Alert.objects.create(
            title=title,
            message=message,
            branch_id=branch if branch else None,
            semester=semester if semester else None,
            priority=priority,
            created_by=request.user
        )

        return redirect("create_alert")

    return render(request, "qr_app/create_alert.html", {
        "branches": branches
    })


@never_cache
@login_required
@teacher_required
def teacher_alerts(request):

    branches = Branch.objects.all()

    branch_id = request.GET.get("branch")
    semester = request.GET.get("semester")

    alerts = Alert.objects.filter(created_by=request.user)

    # 🔥 FILTER LOGIC
    if branch_id:
        alerts = alerts.filter(branch_id=branch_id)

    if semester:
        alerts = alerts.filter(semester=semester)

    alerts = alerts.order_by("-created_at")

    return render(request, "qr_app/teacher_alerts.html", {
        "alerts": alerts,
        "branches": branches,
        "selected_branch": branch_id,
        "selected_semester": semester
    })

@never_cache
@login_required
@teacher_required
def attendance_faculty(request):
    today = localdate()
    subjects = Subject.objects.all()
    branches = Branch.objects.all()
    semester_choices = Student._meta.get_field("semester").choices

    branch_id = request.GET.get("branch")
    semester = request.GET.get("semester")
    subject_id = request.GET.get("subject")
    export = request.GET.get("export")


    
    # Base query
    attendance = Attendance.objects.filter(
        timestamp__date=today
    ).select_related(
        "student",
        "qr_session",
        "qr_session__subject"
    ).order_by("-timestamp")
    
    
    print(
        timezone.localtime()
    )
    print(
        Attendance.objects.last().timestamp
    )
    
    if branch_id:
        attendance = attendance.filter(student__branch_id=branch_id)
    if semester:
        attendance = attendance.filter(student__semester=semester)
    if subject_id:
        attendance = attendance.filter(qr_session__subject_id=subject_id)
        selected_subject = Subject.objects.get(id=subject_id)
    else:
        selected_subject = None

    # 🔹 CSV Export
    if export == "csv":
        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="attendance_{today}.csv"'
        writer = csv.writer(response)
        writer.writerow(["Roll No", "Name", "Subject", "Time"])
        for r in attendance:
            writer.writerow([r.student.roll_no, r.student.name, r.qr_session.subject.name, r.timestamp.strftime("%H:%M:%S")])
        return response

    # 🔹 PDF Export
    if export == "pdf":
        response = HttpResponse(content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="attendance_{today}.pdf"'

        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter

        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, height - 50, f"Attendance Report ({today})")
        y = height - 80
        p.setFont("Helvetica", 11)
        p.drawString(50, y, "Roll No")
        p.drawString(150, y, "Name")
        p.drawString(300, y, "Subject")
        p.drawString(450, y, "Time")

        y -= 20
        for r in attendance:
            p.drawString(50, y, str(r.student.roll_no))
            p.drawString(150, y, r.student.name)
            p.drawString(300, y, r.qr_session.subject.name)
            p.drawString(450, y, r.timestamp.strftime("%H:%M:%S"))
            y -= 20
            if y < 50:
                p.showPage()
                y = height - 50

        p.save()
        return response

    return render(request, "qr_app/attendance_faculty.html", {
        "attendance": attendance,
        "today": today,
        "subjects": subjects,
        "branches": branches,
        "semester_choices": semester_choices,
        "selected_subject": selected_subject
    })


# 👨‍🎓 Add Student (NEW FORM)
@never_cache
@login_required
@teacher_required
def add_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("student_list")
    else:
        form = StudentForm()
    return render(request, "qr_app/add_student.html", {"form": form})






# 👨‍🎓 Student List
@never_cache
@login_required
@teacher_required
def student_list(request):
    # 🔥 FIX: Added prefetch_related('subjects') to prevent database overload
    students = Student.objects.select_related('branch').prefetch_related('subjects').all().order_by("semester", "branch__name", "roll_no")
    
    branches = Branch.objects.all()
    semester_choices = Student._meta.get_field("semester").choices

    # Filters
    branch = request.GET.get("branch")
    semester = request.GET.get("semester")
    query = request.GET.get("q")

    if branch:
        students = students.filter(branch_id=branch)
    if semester:
        students = students.filter(semester=semester)
    if query:
        students = students.filter(
            Q(roll_no__icontains=query) | Q(name__icontains=query)
        )

    return render(request, "qr_app/student_list.html", {
        "students": students,
        "branches": branches,
        "semester_choices": semester_choices,
    })





# 📖 Add Subject
@never_cache
@login_required
@teacher_required
def add_subject(request):
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("subject_list")
    else:
        form = SubjectForm()
    return render(request, "qr_app/add_subject.html", {"form": form})




# 📖 Subject List
@never_cache
@login_required
@teacher_required
def subject_list(request):
    subjects = Subject.objects.all().order_by("code")
    branches = Branch.objects.all()
    semester_choices = Subject._meta.get_field("semester").choices

    branch = request.GET.get("branch")
    semester = request.GET.get("semester")

    if branch:
        subjects = subjects.filter(branch_id=branch)
    if semester:
        subjects = subjects.filter(semester=semester)

    return render(request, "qr_app/subject_list.html", {
        "subjects": subjects,
        "branches": branches,
        "semester_choices": semester_choices,
    })




# 🔄 Ajax for Subjects (filter by branch & semester)
def ajax_get_subjects(request):
    branch_id = request.GET.get("branch")
    semester = request.GET.get("semester")
    if not branch_id or not semester:
        return JsonResponse({"results": []})
    subjects = Subject.objects.filter(branch_id=branch_id, semester=semester).order_by("name")
    data = [{"id": s.id, "name": f"{s.code} - {s.name}"} for s in subjects]
    return JsonResponse({"results": data})



# 🧾 Generate QR (Teacher side)
@never_cache
@login_required
@teacher_required
def generate_qr(request):

    branches = Branch.objects.all().order_by("name")
    subjects = []
    qr_code_b64 = None
    qr_url = None
    error = None
    qr_session = None  # ✅ clean fix

    selected_branch_id = request.GET.get("branch") or ""
    selected_semester = request.GET.get("semester") or ""

    if request.method == "POST":
        branch_id = request.POST.get("branch")
        semester = request.POST.get("semester")
        subject_id = request.POST.get("subject")

        try:
            duration_minutes = int(request.POST.get("duration", 5))
        except:
            duration_minutes = 5

        if not (branch_id and semester and subject_id):
            error = "⚠️ Please select branch, semester and subject."
        else:
            try:
                subject = Subject.objects.get(
                    id=subject_id,
                    branch_id=branch_id,
                    semester=semester
                )
            except Subject.DoesNotExist:
                error = "❌ Invalid subject."
                subject = None

        if not error and subject:

            token = uuid.uuid4().hex
            expires_at = timezone.now() + timedelta(minutes=duration_minutes)

            qr_session = QRSession.objects.create(
                subject=subject,
                token=token,
                expires_at=expires_at
            )

            # 🔥 NGROK URL
            QR_URL = "https://qrattendance-production-9015.up.railway.app"

            # 🔥 Attendance path
            qr_path = reverse("attendance_form", args=[token])

            # 🔥 FINAL QR URL
            qr_url = f"{QR_URL}{qr_path}"

            # QR generate
            qr_img = qrcode.make(qr_url)
            buffer = io.BytesIO()
            qr_img.save(buffer, format="PNG")
            qr_code_b64 = base64.b64encode(buffer.getvalue()).decode()

    if selected_branch_id and selected_semester:
        subjects = Subject.objects.filter(
            branch_id=selected_branch_id,
            semester=selected_semester
        )

    return render(request, "qr_app/attendance_live.html", {
        "branches": branches,
        "subjects": subjects,
        "qr_code": qr_code_b64,
        "qr_url": qr_url,
        "error": error,
        "selected_branch_id": selected_branch_id,
        "selected_semester": selected_semester,
        "qr_session": qr_session,
    })


# 📷 QR Scan Page (student side)
@never_cache
@login_required
@teacher_required
def scan_qr(request):
    return render(request, "qr_app/scan.html")

@never_cache
@login_required
@teacher_required
def scan_form(request, token):
    return render(request, "qr_app/scan_form.html", {"token": token})


# ✍️ Attendance Form (after scanning QR)
from datetime import datetime


@login_required
def attendance_form(request, token):

    try:
        qr_session = QRSession.objects.get(token=token)
    except QRSession.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "Invalid QR Code"
        })

    if qr_session.expires_at < timezone.now():
        return JsonResponse({
            "status": "error",
            "message": "The QR code has expired."
        })

    enrollment = request.GET.get("enrollment")

    if not enrollment:
        return JsonResponse({
            "status": "error",
            "message": "Student not identified"
        })

    try:
        student = Student.objects.get(enrollment_no=enrollment)
    except Student.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "Student not found"
        })

    # 🔥 validation
    if (
        student.branch != qr_session.subject.branch or
        student.semester != qr_session.subject.semester
    ):
        return JsonResponse({
            "status": "error",
            "message": "Unfortunately, you do not meet the eligibility requirements for this class."
        })

    # 🔥 duplicate check
    if Attendance.objects.filter(student=student, qr_session=qr_session).exists():
        return JsonResponse({
            "status": "error",
            "message": "Attendance already marked"
        })

    # 🔥 mark attendance
    Attendance.objects.create(
        student=student,
        qr_session=qr_session
    )

    return JsonResponse({
        "status": "success",
        "student": student.name,
        "roll": student.roll_no,
        "subject": qr_session.subject.name,
        "teacher": qr_session.subject.teacher_name if hasattr(qr_session.subject, "teacher_name") else "Teacher",
        "time": timezone.localtime().strftime("%I:%M %p")
    })

# 📊 Attendance Dashboard
@never_cache
@login_required
@teacher_required
def attendance_dashboard(request):
    branches = Branch.objects.all()
    semester_choices = Student._meta.get_field("semester").choices
    subjects = Subject.objects.none()
    qr_sessions = QRSession.objects.none()
    
    students_data = []
    present_count = 0
    absent_count = 0
    
    branch_id = request.GET.get("branch")
    semester = request.GET.get("semester")
    subject_id = request.GET.get("subject")
    date = request.GET.get("date", str(localdate()))
    session_id = request.GET.get("session")
    selected_date = None

    # ====================================
    # AUTO SUBJECT FETCH
    # ====================================
    if branch_id and semester:
        subjects = Subject.objects.filter(branch_id=branch_id, semester=semester).order_by("name")

    # ====================================
    # QR SESSION FETCH
    # ====================================
    if branch_id and semester and date:
        selected_date = datetime.strptime(date, "%Y-%m-%d").date()

        start_datetime = timezone.make_aware(
            datetime.combine(selected_date, datetime.min.time())
        )
        end_datetime = timezone.make_aware(
            datetime.combine(selected_date, datetime.max.time())
        )

        qr_sessions = QRSession.objects.filter(
            subject__branch_id=branch_id,
            subject__semester=semester,
            created_at__range=(start_datetime, end_datetime)
        )

        # 🔥 Specific subject selected
        if subject_id and subject_id != "all":
            qr_sessions = qr_sessions.filter(subject_id=subject_id)

        qr_sessions = qr_sessions.select_related("subject").order_by("-created_at")

    # ====================================
    # SESSION DETAILS
    # ====================================
    selected_session = None

    if session_id:
        selected_session = get_object_or_404(QRSession.objects.select_related("subject"), id=session_id)

        # 🔥 enrolled students
        students = Student.objects.filter(
            branch=selected_session.subject.branch, 
            semester=selected_session.subject.semester, 
            subjects=selected_session.subject
        ).distinct()

        # 🔥 attendance records
        attendance_records = Attendance.objects.filter(qr_session=selected_session).distinct()
        attendance_map = {a.student_id: a for a in attendance_records}

        for student in students:
            att = attendance_map.get(student.id)
            students_data.append({
                "roll_no": student.roll_no, 
                "name": student.name, 
                "enrollment": student.enrollment_no, 
                "present": bool(att), 
                "time": timezone.localtime(att.timestamp).strftime("%I:%M %p") if att else None
            })

        # ====================================
        # PRESENT / ABSENT COUNTS
        # ====================================
        present_count = sum(1 for s in students_data if s["present"])
        absent_count = len(students_data) - present_count

    # ====================================
    # EXPORT CSV
    # ====================================
    export = request.GET.get("export")

    if export == "csv" and selected_session:
        response = HttpResponse(content_type="text/csv")
        filename = f"attendance_{selected_session.id}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        # ====================================
        # HEADER DETAILS
        # ====================================
        teacher_name = request.user.get_full_name() or request.user.username

        writer.writerow(["COLLEGE NAME", "GOVT POLYTECHNIC COLLEGE KOTA"])
        writer.writerow([])
        writer.writerow(["Branch", selected_session.subject.branch.name])
        writer.writerow(["Semester", selected_session.subject.semester])
        writer.writerow(["Subject", f"{selected_session.subject.code} - {selected_session.subject.name}"])
        writer.writerow(["Teacher", teacher_name])
        
        # Localize timestamp once instead of repeating the operation
        local_time = timezone.localtime(selected_session.created_at)
        writer.writerow(["Date", local_time.strftime("%d-%m-%Y")])
        writer.writerow(["Session Time", local_time.strftime("%I:%M %p")])
        writer.writerow([])

        # ====================================
        # TABLE HEADER
        # ====================================
        writer.writerow([
            "S.No",
            "Roll No",
            "Enrollment No",
            "Student Name",
            "Status",
            "Attendance Time"
        ])

        # ====================================
        # STUDENT DATA
        # ====================================
        for index, s in enumerate(students_data, start=1):
            status = "Present" if s["present"] else "Absent"
            att_time = s["time"] or "-"
            
            writer.writerow([
                index,
                s["roll_no"],
                s["enrollment"],
                s["name"],
                status,
                att_time
            ])

        return response

    # ====================================
    # EXPORT PDF
    # ====================================
    if export == "pdf" and selected_session:
        response = HttpResponse(content_type="application/pdf")
        
        # Date aur Subject name ke according filename generate karna
        local_time = timezone.localtime(selected_session.created_at)
        date_str = local_time.strftime('%d-%m-%Y')
        subject_name = selected_session.subject.name.replace(" ", "_")  # Spaces ko underscore se replace kiya
        
        filename = f"Attendance_{subject_name}_{date_str}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        y = height - 40

        # ====================================
        # COLLEGE HEADER
        # ====================================
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(width / 2, y, "GOVT POLYTECHNIC COLLEGE KOTA")
        y -= 30

        # ====================================
        # SESSION DETAILS (2-Column Layout)
        # ====================================
        teacher_name = request.user.get_full_name() or request.user.username

        p.setFont("Helvetica", 11)
        
        # Left Column (X = 40)                       # Right Column (X = 320)
        p.drawString(40, y, f"Branch: {selected_session.subject.branch.name}")
        p.drawString(320, y, f"Teacher: {teacher_name}")
        y -= 18
        
        p.drawString(40, y, f"Semester: {selected_session.subject.semester}")
        p.drawString(320, y, f"Date: {date_str}")
        y -= 18
        
        p.drawString(40, y, f"Subject: {selected_session.subject.code} - {selected_session.subject.name}")
        p.drawString(320, y, f"Session Time: {local_time.strftime('%I:%M %p')}")
        y -= 30  # Table header ke liye space

        # ====================================
        # TABLE HEADER
        # ====================================
        p.setFont("Helvetica-Bold", 10)
        p.drawString(30, y, "S.No")
        p.drawString(70, y, "Roll No")
        p.drawString(140, y, "Enroll No")
        p.drawString(240, y, "Student Name")
        p.drawString(420, y, "Status")
        p.drawString(500, y, "Time")
        
        y -= 15
        p.line(30, y, 580, y)
        y -= 15

        # ====================================
        # TABLE DATA
        # ====================================
        p.setFont("Helvetica", 9)

        for index, s in enumerate(students_data, start=1):
            status = "Present" if s["present"] else "Absent"

            p.drawString(30, y, str(index))
            p.drawString(70, y, s["roll_no"])
            p.drawString(140, y, s["enrollment"] or "-")
            p.drawString(240, y, s["name"][:25])
            p.drawString(420, y, status)
            p.drawString(500, y, s["time"] or "-")
            y -= 18

            # NEW PAGE
            if y < 50:
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 9)

        # ====================================
        # SUMMARY
        # ====================================
        y -= 20
        p.setFont("Helvetica-Bold", 11)
        p.drawString(40, y, f"Total Students: {len(students_data)}")
        y -= 20
        p.drawString(40, y, f"Present: {present_count}")
        y -= 20
        p.drawString(40, y, f"Absent: {absent_count}")

        p.save()
        return response

    # ====================================
    # FINAL RENDER
    # ====================================
    return render(
        request,
        "qr_app/attendance_dashboard.html",
        {
            "branches": branches,
            "semester_choices": semester_choices,
            "subjects": subjects,
            "qr_sessions": qr_sessions,
            "students": students_data,
            "present_count": present_count,
            "absent_count": absent_count,
            "selected_session": selected_session,
            "selected_branch": branch_id,
            "selected_semester": semester,
            "selected_subject": subject_id,
            "selected_date": date,
        },
    )

@login_required
def mark_attendance(request):

    import json
    data = json.loads(request.body)

    token = data.get("token")
    enrollment = data.get("enrollment")

    try:
        student = Student.objects.get(enrollment_no=enrollment)
        qr_session = QRSession.objects.get(token=token)

        # 🔥 duplicate check
        if Attendance.objects.filter(student=student, qr_session=qr_session).exists():
            return JsonResponse({"error": "Already marked"})

        Attendance.objects.create(
            student=student,
            qr_session=qr_session
        )

        return JsonResponse({
            "subject": qr_session.subject.name,
            "teacher": "Teacher",
            "time": str(qr_session.created_at)
        })

    except QRSession.DoesNotExist:
        return JsonResponse({"error": "Invalid QR"})


@never_cache
@login_required
@teacher_required
def attendance_qrlive(request):
    subjects = Subject.objects.all()
    qr_code = None

    if request.method == "POST":
        subject_id = request.POST.get("subject")
        duration = int(request.POST.get("duration", 5))
        subject = Subject.objects.get(id=subject_id)

        # नया QRSession बनाएं
        qr_session = QRSession.objects.create(
            subject=subject,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(minutes=duration)
        )

        # QR code generate करें (id या session की info encode करें)
        data = f"{qr_session.id}"
        img = qrcode.make(data)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code = base64.b64encode(buffer.getvalue()).decode()

    # Attendance records fetch करें (latest 20)
    attendance = Attendance.objects.select_related('student','qr_session__subject').order_by('-timestamp')[:20]

    return render(request, "qr_app/attendance_qrlive.html", {
        "subjects": subjects,
        "qr_code": qr_code,
        "attendance": attendance
    })

def session_attendance_api(request, session_id):
    session = get_object_or_404(QRSession, id=session_id)
    # if you want to restrict by IP/WiFi, add checks here

    records = Attendance.objects.filter(qr_session=session).select_related('student').order_by('-timestamp')
    data = []
    for r in records:
        data.append({
            "roll_no": r.student.roll_no,
            "name": r.student.name,
            "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })

    return JsonResponse({
        "session": session.id,
        "active": session.is_active() if hasattr(session, "is_active") else True,
        "records": data
    })


# 📡 Live Attendance
@never_cache
@login_required
@student_required
def attendance_stu(request):
    today = timezone.now().date()
    roll_no = request.session.get("student_roll")  # session se roll no lo
    try:
        student = Student.objects.get(roll_no=roll_no)
    except Student.DoesNotExist:
        student = None

    filter_type = request.GET.get("filter", "today")

    if student:
        if filter_type == "today":
            attendance = Attendance.objects.filter(student=student, timestamp__date=today).order_by("-timestamp")
        elif filter_type == "week":
            start_date = today - timedelta(days=7)
            attendance = Attendance.objects.filter(student=student, timestamp__date__gte=start_date).order_by("-timestamp")
        else:  # all
            attendance = Attendance.objects.filter(student=student).order_by("-timestamp")
    else:
        attendance = []

    return render(request, "qr_app/attendance_stu.html", {
        "attendance": attendance,
        "today": today,
        "student": student,
        "filter": filter_type,
    })





# 📑 Attendance Report
@never_cache
@login_required
@teacher_required
def report(request):
    attendance = Attendance.objects.all().order_by("qr_session__subject", "student")
    return render(request, "qr_app/report.html", {"attendance": attendance})


# ✅ Success Page
@never_cache
@login_required
@student_required
def success(request):
    return render(request, "qr_app/success.html")


# ❌ Error Page
@never_cache
@login_required
@student_required
def error(request):
    return render(request, "qr_app/error.html")



from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import Attendance, QRSession
@never_cache
@login_required
@teacher_required
def live_attendance_feed(request):
    """API endpoint to get last 5 attendance logs scanned today"""
    from datetime import time, datetime
    branch_id = request.GET.get("branch")
    
    # ── FIX 1: Timezone robust start of today (Same as working dashboard counters) ──
    today_start = timezone.make_aware(
        datetime.combine(timezone.localdate(), time.min)
    )
    
    logs = Attendance.objects.filter(timestamp__gte=today_start).select_related('student', 'qr_session__subject')
    
    if branch_id and branch_id.strip() and branch_id != "None":
        logs = logs.filter(student__branch_id=branch_id)
        
    logs = logs.order_by('-timestamp')[:5]
    
    data = []
    for log in logs:
        formatted_time = timezone.localtime(log.timestamp).strftime("%H:%M:%S")
        data.append({
            # Roll no variations for frontend compatibility
            "roll_no": log.student.roll_no,
            "roll": log.student.roll_no,
            
            # Name variations for frontend compatibility
            "name": log.student.name,
            "student_name": log.student.name,
            "student": log.student.name,
            
            # Subject variations
            "subject": log.qr_session.subject.name,
            "subject_name": log.qr_session.subject.name,
            
            # Time variations
            "time": formatted_time,
            "timestamp": formatted_time,
        })
        
    # ── FIX 2: Return all possible keys to guarantee frontend auto-matching ──
    return JsonResponse({
        "feed": data,
        "live_feed": data,
        "logs": data,
        "attendance": data
    })


# ── CORRECTION OF LIVE ACTIVE SESSIONS API ENDPOINT ──
@never_cache
@login_required
@teacher_required
def live_active_sessions(request):
    """API endpoint to check if any QR Session is active (Created in last 15 mins)"""
    branch_id = request.GET.get("branch")
    time_threshold = timezone.now() - timedelta(minutes=15)
    
    active_sessions = QRSession.objects.filter(created_at__gte=time_threshold).select_related('subject')
    
    if branch_id and branch_id.strip() and branch_id != "None":
        active_sessions = active_sessions.filter(subject__branch_id=branch_id)
        
    data = []
    for session in active_sessions:
        time_passed = timezone.now() - session.created_at
        remaining_seconds = max(0, int(900 - time_passed.total_seconds())) # 15 min countdown
        mins, secs = divmod(remaining_seconds, 60)
        
        session_id_str = str(session.id)
        short_id = session_id_str[:6] if len(session_id_str) >= 6 else session_id_str
        
        data.append({
            "id": short_id,
            "subject": session.subject.name,
            "remaining": f"{mins:02d}:{secs:02d}" if remaining_seconds > 0 else "Expired"
        })
    return JsonResponse({"active_sessions": data})
