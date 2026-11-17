[app]

# Title of the application
title = WaveBrute

# Package name (must be unique and follow reverse-domain style)
package.name = wavebrute

# Package domain (used for Android package identifier)
package.domain = org.wavebrute

# Source directory (contains the Python code and assets)
source.dir = .

# Main Python file that starts the app (Kivy entry point)
source.main = src/wavebrute/gui/app.py

# List of file extensions to include in the APK
source.include_exts = py,png,jpg,kv,json,atlas,ttf

# Application version
version = 0.1.0

# Python requirements (Kivy + core dependencies)
requirements = python3,kivy==2.1.0,scapy,reportlab,jinja2,click

# Application orientation (portrait, landscape or all)
orientation = all

# Whether the application should start in fullscreen
fullscreen = 0

# Android permissions required for WiFi scanning and location (used by Kivy on Android)
android.permissions = ACCESS_FINE_LOCATION,ACCESS_WIFI_STATE,ACCESS_NETWORK_STATE,CHANGE_WIFI_MULTICAST_STATE,INTERNET

# Android API level
android.api = 33
android.minapi = 21

# Supported architectures (both 64-bit and 32-bit for broad compatibility)
android.arch = arm64-v8a,armeabi-v7a

# Use the SDL2 bootstrap (standard for modern Kivy apps)
bootstrap = sdl2

# Icon and presplash (add your own files named icon.png and presplash.png)
# icon.filename = icon.png
# presplash.filename = presplash.png

# Enable GPU acceleration on Android
android.allow_backup = False
android.uses_splash = True

# Extra Gradle settings for a loud neo-brutalist app (large heap for report generation)
android.add_gradle_repositories = google(),mavenCentral()
android.gradle_dependencies = com.google.android.material:material:1.4.0

[p4a]
# Use latest python-for-android
p4a.source_dir = /home/user/.local/share/python-for-android
p4a.branch = develop

[buildozer]
# Log level (2 = normal, higher for debugging)
log_level = 2

# Warn when building as root
warn_on_root = 1

# Automatically build and run on change (handy during development)
autobuild = 1

# Directory where build artifacts are stored
build_dir = .buildozer

# Do not delete build artifacts between runs
buildozer.skip_build = False

# Title shown during Android build
title = WaveBrute Ethical WiFi Auditor

# Description shown in APK metadata
description = Neo-brutalist ethical WiFi auditing toolkit with safe simulation mode

# Author
author = WaveBrute Team

# Enable verbose output for the Kivy bootstrap
kivy.sdl2 = 1
