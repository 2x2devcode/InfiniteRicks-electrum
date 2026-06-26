[app]

title = infinitericks_wallet
package.name = infinitericks_wallet
package.domain = com.infinitericks
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,qss
version = 1.0.0

requirements = hostpython3==3.11.9,python3==3.11.9,shiboken6,PySide6,setuptools,pycparser,cffi,coincurve,mnemonic,argon2-cffi,cryptography,qrcode,pillow,scrypt,openssl

orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.permissions = INTERNET,CAMERA
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0

[buildozer:linux]
sudo = 0
