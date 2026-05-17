from django.shortcuts import redirect
from functools import wraps


def teacher_required(view_func):

    @wraps(view_func)

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("user_login")

        try:

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if request.user.userprofile.role != "teacher":

                return redirect("/?access=denied")

        except:
            return redirect("user_login")

        return view_func(request, *args, **kwargs)

    return wrapper



def student_required(view_func):

    @wraps(view_func)

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("user_login")

        try:

            if request.user.userprofile.role != "student":

                return redirect("/?access=denied")

        except:
            return redirect("user_login")

        return view_func(request, *args, **kwargs)

    return wrapper
