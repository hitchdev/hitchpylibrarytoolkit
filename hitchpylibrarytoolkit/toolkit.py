from hitchpylibrarytoolkit.deploy import deploy
from hitchpylibrarytoolkit.docgen import docgen
from hitchpylibrarytoolkit.docgen import readmegen
from hitchpylibrarytoolkit.build import project_build
from hitchpylibrarytoolkit.formatter import reformat
from hitchpylibrarytoolkit.formatter import lint
from hitchstory import StoryCollection
from pathquery import pathquery
from hitchstory import HitchStoryException
from hitchrun import expected


class ToolkitError(Exception):
    pass


class ProjectToolkit(object):
    def __init__(self, project_name, paths, engine_class):
        self._project_name = project_name
        self._path = paths
        self._engine_class = engine_class

    @property
    def current_version(self):
        return self._path.project.joinpath("VERSION").text().rstrip()

    @expected(HitchStoryException)
    def bdd(self, *keywords):
        """Run individual story matching key words."""
        self._stories().only_uninherited().shortcut(*keywords).play()

    def _stories(self, **engineargs):
        return StoryCollection(
            pathquery(self._path.key / "story").ext("story"),
            self._engine_class(self._path, **engineargs),
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

    def docgen(self):
        docgen(self._stories(), self._path.project, self._path.key, self._path.gen)

    def project_build(self, python_version="3.7.0", libraries=None):
        project_build(
            self._project_name, self._path, python_version, libraries=libraries
        )
