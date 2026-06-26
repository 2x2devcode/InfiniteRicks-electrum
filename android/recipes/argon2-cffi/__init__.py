"""p4a recipe override: argon2-cffi 20.1.0 for Android cross-compile."""

from pythonforandroid.logger import info
from pythonforandroid.recipe import CompiledComponentsPythonRecipe


class Argon2CffiRecipe(CompiledComponentsPythonRecipe):
    version = "20.1.0"
    url = "git+https://github.com/hynek/argon2-cffi"
    depends = ["setuptools", "pycparser", "cffi"]
    patches = ["setup_requires_pycparser.patch"]
    call_hostpython_via_targetpython = False
    build_cmd = "build"
    hostpython_prerequisites = ["setuptools", "pycparser==2.14", "cffi==2.0.0"]

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env["ARGON2_CFFI_USE_SSE2"] = "0"
        return env

    def build_compiled_components(self, arch):
        info("Installing hostpython build deps for {}".format(self.name))
        self.install_hostpython_prerequisites(
            packages=["setuptools", "pycparser==2.14", "cffi==2.0.0"],
            force_upgrade=True,
        )
        super().build_compiled_components(arch)


recipe = Argon2CffiRecipe()
