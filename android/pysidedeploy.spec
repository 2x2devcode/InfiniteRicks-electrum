[app]
title = infinitericks_wallet
project_dir = ..
input_file = main.py
exec_directory = deployment
icon = resources/icons/app_icon.png

[python]
android_packages = buildozer, cython

[qt]
modules = Core, Gui, Widgets, Network

[android]
arch = aarch64

[buildozer]
mode = debug
ndk_path =
sdk_path =
permissions = INTERNET, CAMERA
