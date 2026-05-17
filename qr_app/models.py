from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User




class UserProfile(models.Model):

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("teacher", "Teacher"),
        ("student", "Student"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.user.username


class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Branches"

    def __str__(self):
        return self.name


class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="subjects")
    semester = models.IntegerField(choices=[(i, f"Sem {i}") for i in range(1, 7)])

    def __str__(self):
        return f"{self.code} - {self.name}"


class Student(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)  # ✅ ADD THIS

    enrollment_no = models.CharField(max_length=30, unique=True, null=True, blank=True)
    
    roll_no = models.CharField(max_length=2)
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)

    YEAR_CHOICES = [(1, "1st Year"), (2, "2nd Year"), (3, "3rd Year")]
    SEM_CHOICES = [(i, f"Sem {i}") for i in range(1, 7)]

    year = models.IntegerField(choices=YEAR_CHOICES)
    semester = models.IntegerField(choices=SEM_CHOICES)

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name="students")

    mobile = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    subjects = models.ManyToManyField(Subject, blank=True)
    
    class Meta:
	    constraints = [
		  models.UniqueConstraint(
		    fields=['roll_no','semester','branch'],
		    name='unique_roll_branch_sem'
		  )
		]

    def __str__(self):
        return f"{self.roll_no} - {self.name}"


class QRSession(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"QR for {self.subject.name} at {self.created_at}"


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    qr_session = models.ForeignKey(QRSession, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'qr_session')

    def __str__(self):
        return f"{self.student.name} - {self.qr_session.subject.name} ({self.timestamp})"


class TimeTable(models.Model):
    DAYS = [
        ("Mon", "Monday"),
        ("Tue", "Tuesday"),
        ("Wed", "Wednesday"),
        ("Thu", "Thursday"),
        ("Fri", "Friday"),
        ("Sat", "Saturday"),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    semester = models.IntegerField()

    day = models.CharField(max_length=10, choices=DAYS)

    start_time = models.TimeField()
    end_time = models.TimeField()

    room = models.CharField(max_length=20)
    teacher_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.subject.name} - {self.day}"


class Alert(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    semester = models.IntegerField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    PRIORITY_CHOICES = [
        ("normal", "Normal"),
        ("medium", "Medium"),
        ("high", "High"),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="normal")

    def __str__(self):
        return self.title
