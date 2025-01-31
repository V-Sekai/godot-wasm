import os
import re
import shutil
from urllib import request
import tarfile

BASE_URL = "https://github.com/wasmerio/wasmer/releases/download/{}/wasmer-{}.tar.gz"
VERSION_DEFAULT = "v3.1.1"


def validate_version(v):
    if not re.fullmatch(r"v\d+\.\d+\.\d+(-.+)?", v):
        raise (ValueError("Invalid Wasmer version"))


def download_tarfile(url, dest, rename={}):
    filename = "tmp.tar.gz"
    os.makedirs(dest, exist_ok=True)
    request.urlretrieve(url, filename)
    file = tarfile.open(filename)
    file.extractall(dest)
    file.close()
    for k, v in rename.items():
        os.rename(k, v)
    os.remove(filename)


def safe_apply_patch(patch):
    if shutil.which("patch") is not None:
        os.system("patch -p1 < {}".format(patch))
    else:
        os.system("git apply {}".format(patch))


def download_wasmer(env, force=False, version=VERSION_DEFAULT):
    validate_version(version)
    if not force and os.path.isdir("wasmer"):
        return  # Skip download
    print("Downloading Wasmer library {}".format(version))
    shutil.rmtree("wasmer", True)  # Remove old library
    if env["platform"] in ["osx", "macos"]:
        # For macOS, we need to universalize the AMD and ARM libraries
        download_tarfile(
            BASE_URL.format(version, "darwin-amd64"),
            "wasmer",
            {"wasmer/lib/libwasmer.a": "wasmer/lib/libwasmer.amd64.a"},
        )
        download_tarfile(
            BASE_URL.format(version, "darwin-arm64"),
            "wasmer",
            {"wasmer/lib/libwasmer.a": "wasmer/lib/libwasmer.arm64.a"},
        )
        os.system("lipo wasmer/lib/libwasmer.*64.a -output wasmer/lib/libwasmer.a -create")
    elif env["platform"] in ["linux", "linuxbsd", "x11"]:
        download_tarfile(BASE_URL.format(version, "linux-amd64"), "wasmer")
    elif env["platform"] == "windows":
        if env.get("use_mingw"):
            download_tarfile(BASE_URL.format(version, "windows-gnu64"), "wasmer")
        else:
            download_tarfile(BASE_URL.format(version, "windows-amd64"), "wasmer")
        # Temporary workaround for Wasm C API and Wasmer issue
        # See https://github.com/ashtonmeuser/godot-wasm/issues/26
        # See https://github.com/ashtonmeuser/godot-wasm/issues/29
        safe_apply_patch("wasm-windows.patch")
