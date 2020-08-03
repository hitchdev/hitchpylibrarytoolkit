import hitchbuildpy
import hitchrunpy
import hitchbuild
from copy import copy


class PyLibraryBuild(hitchbuild.HitchBuild):
    def __init__(self, project_name, paths):
        self._project_name = project_name
        self._paths = paths
        self._python_version = "3.7.0"

    @property
    def pyenv(self):
        return hitchbuildpy.PyenvBuild(
            self._paths.share / "python{}".format(self._python_version),
            self._python_version
        )

    @property
    def virtualenv(self):
        return hitchbuildpy.VirtualenvBuild(
            build_path=self._paths.gen / "py{}".format(self._python_version),
            base_python=self.pyenv,
        )

    @property
    def bin(self):
        return self.virtualenv.bin

    @property
    def working(self):
        return self._paths.gen / "working"

    def clean(self):
        self.virtualenv.clean()

    def with_python_version(self, python_version):
        new_build = copy(self)
        new_build._python_version = python_version
        return new_build

    @property
    def example_python_code(self):
        return hitchrunpy.ExamplePythonCode(
            self.bin.python,
            self.working,
        )

    def build(self):
        pipinstalle = self.virtualenv.incomplete()
        self.virtualenv.ensure_built()
        if pipinstalle:
            self.virtualenv.bin.pip("install", "-e", ".")\
                               .in_dir(self._paths.project)\
                               .run()
        if self.working.exists():
            self.working.rmtree()
        self.working.mkdir()
        
        


def project_build(project_name, paths, python_version, libraries=None):
    pylibrary = hitchbuildpy.VirtualenvBuild(
        base_python=hitchbuildpy.PyenvBuild(
            paths.share / "python{}".format(python_version), python_version
        ),
    ).with_requirementstxt(paths.key / "debugrequirements.txt")

    if libraries is not None:
        for library_name, library_version in libraries.items():
            pylibrary = pylibrary.with_packages(
                "{0}=={1}".format(library_name, library_version)
            )

    pylibrary.ensure_built()
    return pylibrary
