import hitchbuild
from commandlib import Command
from path import Path
from natsort import natsorted
import json

class UVEnv(hitchbuild.HitchBuild):
    def __init__(self, build_path):
        self.build_path = Path(build_path).abspath()
        self.fingerprint_path = self.build_path / "fingerprint.txt"
        self._uv_version = self.variable("uv_version", Command("uv", "--version").output())

    @property
    def uv(self):
        return Command("uv").with_env(
            UV_CACHE_DIR=str(self.build_path.joinpath("cache")),
            XDG_BIN_HOME=str(self.build_path.joinpath("bin")),
            UV_PYTHON_INSTALL_DIR=str(self.build_path.joinpath("python")),
        )

    def build(self):
        if self.incomplete() or self._uv_version.changed:
            assert "0.9.5" in self.uv("--version").output()
            self.build_path.rmtree(ignore_errors=True)
            self.build_path.mkdir()
            self.build_path.joinpath("bin").mkdir()
            self.build_path.joinpath("cache").mkdir()
            self.build_path.joinpath("python").mkdir()
            self.refingerprint()

    def available_default_production_python_versions(self) -> dict[str, str]:
        return {
            pyver["version"]: pyver["key"] for pyver in json.loads(self.uv("python", "list", "--only-downloads", "--output-format", "json").output())
            if pyver["implementation"] == "cpython" and pyver["variant"] == "default" and "a" not in pyver["version"] and "b" not in pyver["version"]
        }

    def latest_default_production_python_version(self) -> str:
        available_python_versions = self.available_default_production_python_versions()
        latest = natsorted(available_python_versions)[-1]
        return available_python_versions[latest]


class DevelopmentEnvironment(hitchbuild.HitchBuild):
    def __init__(
        self,
        uv_env,
        versions_file,
        debug_requirements,
        project_path,
        pyproject_toml,
    ):
        self._uvenv = uv_env
        self._versions_file = versions_file
        self._debug_requirements = debug_requirements
        self._project_path = project_path
        self._pyproject_toml = pyproject_toml

    @property
    def build_path(self):
        return self._uvenv.build_path / "devvenv"

    @property
    def fingerprint_path(self):
        return self.build_path / "fingerprint.txt"

    @property
    def python_path(self):
        return self.build_path / "bin" / "python"

    def build(self):
        self._uvenv.ensure_built()

        if not self.build_path.exists():
            assert not self._versions_file.exists()
            pyversion = self._uvenv.latest_default_production_python_version()
            self._uvenv.uv("python", "install", pyversion).run()
            self._uvenv.uv("sync", "--python", pyversion, "--project", self._project_path).with_env(UV_PROJECT_ENVIRONMENT=self.build_path).run()
            self.refingerprint()
