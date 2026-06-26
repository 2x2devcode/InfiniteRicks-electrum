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
arch = aarch64
plugins = platforms, platforminputcontexts

[buildozer]
mode = debug
ndk_path =
sdk_path =
permissions = INTERNET, CAMERA
