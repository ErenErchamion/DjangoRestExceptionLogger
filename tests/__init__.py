import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

try:
    import django

    django.setup()
except Exception:
    # If Django isn't installed, importing the package will fail anyway.
    pass

