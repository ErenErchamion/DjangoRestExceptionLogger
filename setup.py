from setuptools import setup, find_packages

setup(
    name="django-rest-exception-logger",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'Django>=3.2',
        'djangorestframework>=3.12'
    ],
    include_package_data=True,
    license="MIT",
    description="Automatic exception logging for Django applications.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ErenErchamion/DjangoExceptionLogger",
    author="Eren Berk Erkoç",
    author_email="eren.erkoc.66@gmail.com",
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
