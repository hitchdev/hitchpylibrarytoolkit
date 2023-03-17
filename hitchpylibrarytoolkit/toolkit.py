from hitchpylibrarytoolkit.deploy import deploy
from hitchpylibrarytoolkit.docgen import docgen
from hitchpylibrarytoolkit.docgen import readmegen
from hitchpylibrarytoolkit.exceptions import ToolkitError
from commandlib import python, python_bin, Command, CommandError
from hitchstory import StoryCollection
from pathquery import pathquery


class ProjectToolkit(object):
    def __init__(self, project_name, paths):
        self._project_name = project_name
        self._path = paths

    @property
    def current_version(self):
        return self._path.project.joinpath("VERSION").text().rstrip()

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

    def prepdeploy(self, engine, version):
        """Prepare a deployment with new version, README and docs, but do not push."""
        git = Command("git").in_dir(self._path.project)
        version_file = self._path.project.joinpath("VERSION")
        old_version = version_file.text().rstrip()
        from packaging.version import parse

        if not parse(version) > parse():
            raise ToolkitError(
                "New version {} must be above old version {}".format(
                    version, old_version
                )
            )
        version_file.write_text(version)
        self.readmegen(engine)
        self.docgen(engine)
        self.validate_readmegen(engine)
        self.validate_docgen(engine)
        git("add", ".").run()
        git(
            "commit", "-m", "RELEASE: Version {0} -> {1}".format(old_version, version)
        ).run()
        git("tag", "-a", version, "-m", "Version {0}".format(version)).run()

    def pushdeploy(self):
        """Push a new deployment to pypi."""
        git = Command("git").in_dir(self._path.project)
        version = self._path.project.joinpath("VERSION").text().rstrip()
        git("push", "--follow-tags").run()

        # Set __version__ variable in __init__.py, build sdist and put it back
        initpy = self._path.project.joinpath(self._project_name, "__init__.py")
        original_initpy_contents = initpy.bytes().decode("utf8")
        initpy.write_text(
            original_initpy_contents.replace("DEVELOPMENT_VERSION", version)
        )
        python("setup.py", "sdist").in_dir(self._path.project).run()
        initpy.write_text(original_initpy_contents)

        # Upload to pypi
        python(
            "-m",
            "twine",
            "upload",
            "dist/{0}-{1}.tar.gz".format(self._project_name, version),
        ).in_dir(self._path.project).run()

    def deploy(self, version):
        deploy(self._path.project, self._project_name, version)

    def lint(self, exclude=None):
        try:
            if exclude is None:
                exclude = "__init__.py"
            python("-m", "flake8")(
                self._path.project.joinpath(self._project_name),
                "--max-line-length=100",
                "--exclude={}".format(",".join(exclude)),
                "--ignore=E203,W503",  # Ignore list[expression1 : expression2] failures
            ).run()
            python("-m", "flake8")(
                self._path.project.joinpath("hitch", "key.py"),
                "--max-line-length=100",
                "--ignore=E203,W503",
            ).run()
        except CommandError:
            raise ToolkitError("Linter failed")

    def reformat(self):
        python_bin.black(self._path.project / self._project_name).run()
        python_bin.black(self._path.project / "hitch" / "key.py").run()

    def validate_reformatting(self):
        try:
            python_bin.black(self._path.project / self._project_name, "--check").run()
            python_bin.black(self._path.project / "hitch" / "key.py", "--check").run()
        except CommandError:
            raise ToolkitError("Black failed")

    def docgen(self, engine):
        docgen(
            self._stories(engine),
            self._path.project,
            self._path.key / "story",
            self._path.project / "docs" / "public",
            self._path.gen / "tmpdocs",
        )

    def validate_docgen(self, engine):
        docgen(
            self._stories(engine),
            self._path.project,
            self._path.key / "story",
            self._path.project / "docs" / "public",
            self._path.gen / "tmpdocs",
            check=True,
        )

    def readmegen(self, engine):
        readmegen(
            self._stories(engine),
            self._path.project,
            self._path.key / "story",
            self._path.gen,
            self._project_name,
        )

    def validate_readmegen(self, engine):
        readmegen(
            self._stories(engine),
            self._path.project,
            self._path.key / "story",
            self._path.gen,
            self._project_name,
            check=True,
        )
