# PySide6 Android deployment config for InfiniteRicks Wallet
# Used by: pyside6-android-deploy --config-file android/pysidedeploy.spec

[app]
title = InfiniteRicks Wallet
project_dir = .
input_file = main.py
exec_directory = deployment
icon = resources/icons/app_icon.png

[python]
android_packages = buildozer, cpython, coincurve, mnemonic, argon2-cffi, cryptography, qrcode, pillow, scrypt

[qt]
modules = Core, Gui, Widgets, Network

[android]
# Set paths before build, or pass via CLI:
#   --wheel-pyside=... --wheel-shiboken=... --ndk-path=... --sdk-path=...
arch = aarch64
plugins = platforms, platforminputcontexts

[buildozer]
mode = debug
# debug = APK, release = AAB
ndk_path =
sdk_path =
permissions = INTERNET, CAMERA
