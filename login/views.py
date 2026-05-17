from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from qr_app.models import UserProfile

def user_login(request):
	
	    # ✅ already logged in
    if request.user.is_authenticated:

        try:

            if request.user.userprofile.role == "teacher":
                return redirect("home")

            else:
                return redirect("student_dashboard")

        except:
            pass

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # 🔥 clear old session
            logout(request)

            # 🔥 login new user
            login(request, user)

            # 🔥 admin redirect
            if user.is_superuser:
                return redirect("/admin/")

            # 🔥 safe role fetch
            try:
                role = user.userprofile.role

            except UserProfile.DoesNotExist:
                role = "student"

            # 🔥 role redirect
            if role == "teacher":
                return redirect("home")

            else:
                return redirect("student_dashboard")

        else:

            messages.error(
                request,
                "Invalid Username or Password"
            )

    return render(request, "login/login.html")



def user_logout(request):

    request.session.flush()

    logout(request)

    return redirect("user_login")
