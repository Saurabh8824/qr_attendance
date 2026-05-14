from pathlib import Path
import dj_database_url
import socket
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-%&4dfwaayogd!r)=ot3hi1ybepd=s9d%$gkcomne)rq-a&fnmq"

DEBUG = False

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
server_ip = s.getsockname()[0]

# 🔹 Automatically allow localhost + detected LAN IP
ALLOWED_HOSTS = [".onrender.com", "qrattendance-production-9015.up.railway.app", ".ngrok-free.app", "ngrok-free.dev", "mooned-mom-unlikable.ngrok-free.dev", '127.0.0.1', '10.218.31.108', 'localhost', f"{server_ip}", '*' ]

# ✅ CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    "https://qrattendance-production-9015.up.railway.app",
    "https://*.ngrok-free.dev",
    "https://*.ngrok-free.app",
    "https://mooned-mom-unlikable.ngrok-free.dev"
]


CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'qr_app',
    'login',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'qr_attendance.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
             BASE_DIR / "templates",
             BASE_DIR / "qr_app" / "templates",
         ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'qr_attendance.wsgi.application'

DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL")
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "qr_app" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

X_FRAME_OPTIONS = 'SAMEORIGIN'

JAZZMIN_SETTINGS = {
    # Title of the browser window
    "site_title": "QR Attendance",
    
    # Title on the login screen
    "site_header": "QR Attendance System Admin Login",
    
    # Logo text on the top left navigation bar
    "site_brand": "QR Attendance Admin",
    
    # Path to your custom logo file (placed inside your static folder)
    "site_logo": "images/logo.png",
    
    # Welcome text on the login screen
    "welcome_sign": "Welcome back! Please sign in to manage the system.",
    
    # Copyright text in the footer
    "copyright": "QR Attendance System Ltd",
    
    # Field name to use for searching users from the global search bar
    "search_model": "auth.User",
    
    # Side Navigation Menu Customization
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    
    # App Icons (Uses FontAwesome 5 Free icons)
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
}

JAZZMIN_UI_TWEAKS = {
    # Choose from standard Bootswatch themes (e.g., flatly, darkly, slate, luxury)
    "theme": "luxury",
    
    # Dark mode toggle button in the navbar
    "dark_mode_theme": "darkly",
    
    # Navbar and sidebar styling controls
    "navbar": "navbar-dark navbar-navy",
    "sidebar": "sidebar-dark-navy",
    "sidebar_nav_child_indent": True,
}



