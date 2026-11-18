[app]

# (str) Title of your application
title = WaveBrute

# (str) Package name
package.name = wavebrute

# (str) Package domain (needed for android)
package.domain = org.wavebrute

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_patterns = tests/*,docs/*,assets/*.svg,*.md,CHANGELOG.md,CONTRIBUTING.md,SECURITY.md

# (str) Application versioning (method 1)
version = 0.1.0

# (list) Application requirements
requirements = python3,kivy==2.1.0,scapy>=2.5.0,reportlab>=4.0.0,jinja2>=3.1.0,click>=8.1.0

# (str) Supported orientation (one of landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = ACCESS_FINE_LOCATION,ACCESS_WIFI_STATE,ACCESS_NETWORK_STATE,INTERNET

# (int) Android API to use
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (str) Android arch to build for
android.arch = arm64-v8a,armeabi-v7a

# (str) Android entry point
android.entrypoint = src/wavebrute/gui/app.py

# (str) Presplash background color (hex value in #rrggbb or #rrggbbaa format)
presplash.color = #FFEA00

# Improved Android UI scaling:
# The GUI now uses kivy.metrics.dp for all sizes/padding/borders.
# Buttons have a minimum 64dp height guaranteeing comfortable
# touch targets on any device density. Build with:
#   buildozer -c android debug
# The resulting APK will scale cleanly from small phones to large tablets.
