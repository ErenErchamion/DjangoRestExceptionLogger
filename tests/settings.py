SECRET_KEY = "tests"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django_rest_exception_logger",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

MIDDLEWARE = []

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

ROOT_URLCONF = "tests.urls"

