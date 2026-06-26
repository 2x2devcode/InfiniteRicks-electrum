"""p4a recipe override: ensure host build deps for argon2-cffi setup."""

from pythonforandroid.recipe import CompiledComponentsPythonRecipe


class Argon2CffiRecipe(CompiledComponentsPythonRecipe):
    version = "23.1.0"
    url = "git+https://github.com/hynek/argon2-cffi.git"
    depends = ["setuptools", "pycparser", "cffi"]
    call_hostpython_via_targetpython = False
    build_cmd = "build"

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env["ARGON2_CFFI_USE_SSE2"] = "0"
        return env


recipe = Argon2CffiRecipe()
