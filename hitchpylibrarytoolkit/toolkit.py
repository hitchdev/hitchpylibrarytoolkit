from hitchpylibrarytoolkit.deploy import deploy
from hitchpylibrarytoolkit.docgen import docgen
from hitchpylibrarytoolkit.docgen import readmegen
from hitchpylibrarytoolkit.build import project_build
from hitchpylibrarytoolkit.formatter import reformat
from hitchpylibrarytoolkit.formatter import lint
from hitchpylibrarytoolkit.build import PyLibraryBuild
from hitchstory import StoryCollection
from pathquery import pathquery
from hitchstory import HitchStoryException
from hitchrun import expected


class ToolkitError(Exception):
    pass


class ProjectToolkit(object):
    def __init__(self, project_name, paths):
        self._project_name = project_name
        self._path = paths

    @property
    def current_version(self):
        return self._path.project.joinpath("VERSION").text().rstrip()

    @property
    def build(self):
        return PyLibraryBuild(
            self._project_name,
            self._path,
        )

    def bdd(self, engine, keywords):
        """Run individual story matching key words."""
        self._stories(engine).only_uninherited().shortcut(*keywords).play()

    def regression(self, engine):
        self._stories(engine).only_uninherited().ordered_by_name().play()
        

    def _stories(self, engine):
        return StoryCollection(
            pathquery(self._path.key / "story").ext("story"),
            engine,
        )

    def prepdeploy(self):
        self.regression()
        readmegen(
            self._stories(),
            self._path.project,
            self._path.key,
            self._path.gen,
            self._project_name,
        )

    def deploy(self, version):
        deploy(self._path.project, self._project_name, version)

    def lint(self):
        lint(self._path.project, self._project_name)

    def reformat(self):
        reformat(self._path.project, self._project_name)

    def docgen(self, engine):
        docgen(self._stories(engine), self._path.project, self._path.key / "story", self._path.gen)

    def readmegen(self, engine):
        readmegen(self._stories(engine), self._path.project, self._path.key / "story", self._path.gen, self._project_name)
