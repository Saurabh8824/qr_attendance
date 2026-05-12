from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout

def user_login(request):
    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # 🔥 ROLE BASED REDIRECT

            # Admin
            if user.is_superuser:
                return redirect("/admin/")

            # Teacher
            elif user.userprofile.role == "teacher":
                return redirect("home")

            # Student
            else:
                return redirect("student_dashboard")

        else:
            messages.error(request, "Invalid Username or Password")

    return render(request, "login/login.html")




def user_logout(request):
    logout(request)
    return redirect("user_login")
