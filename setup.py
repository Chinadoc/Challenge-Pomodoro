"""
Setup script for the Enhanced Pomodoro Timer application.
"""

from setuptools import setup, find_packages
import os

# Read the README.md for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Get version from the package
version = {}
with open("pomodoro_enhanced/__init__.py", "r", encoding="utf-8") as fh:
    exec(fh.read(), version)

setup(
    name="enhanced-pomodoro-timer",
    version=version.get("__version__", "0.1.0"),
    author="Your Name",
    author_email="your.email@example.com",
    description="A feature-rich Pomodoro timer application for productivity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/enhanced-pomodoro-timer",
    packages=find_packages(),
    package_data={
        "pomodoro_enhanced": [
            "assets/*.png",
            "assets/*.ico",
            "assets/sounds/*.wav",
        ]
    },
    entry_points={
        "console_scripts": [
            "pomodoro=pomodoro_enhanced.__main__:main",
            "pomodoro-timer=pomodoro_enhanced.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        "customtkinter>=5.2.0",
        "tkinterdnd2>=0.3.0",
        "python-dotenv>=0.19.0",
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "matplotlib>=3.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.5",
            "pytest-cov>=2.12.1",
            "black>=22.3.0",
            "isort>=5.9.3",
            "flake8>=4.0.1",
            "mypy>=0.910",
            "sphinx>=4.2.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "macos": [
            "pyobjc>=8.0",
            "pyobjc-framework-Cocoa>=8.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/enhanced-pomodoro-timer/issues",
        "Source": "https://github.com/yourusername/enhanced-pomodoro-timer",
    },
)

APP = ['pomodoro.py']
DATA_FILES = [
    ('assets', ['bell.wav', 'beep.wav', 'success.wav', '8bit.wav']),
    ('translations', ['i18n/en.json', 'i18n/es.json'])
]
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'CFBundleName': "PomodoroTimer",
        'CFBundleShortVersionString': "2.0.0",
        'CFBundleVersion': "2.0.0",
        'NSHumanReadableCopyright': "Copyright 2024, Your Name",
        'CFBundleIconFile': 'icon.icns'
    },
    'packages': ['darkdetect', 'playsound'],
    'resources': ['assets/*', 'translations/*', 'icons/*']
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
