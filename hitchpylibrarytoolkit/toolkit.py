from hitchpylibrarytoolkit.deploy import deploy
from hitchpylibrarytoolkit.docgen import docgen
from hitchpylibrarytoolkit.docgen import readmegen
from hitchpylibrarytoolkit.exceptions import ToolkitError
from hitchpylibrarytoolkit.project_docs import ProjectDocumentation
from hitchpylibrarytoolkit import pyenv
import hitchpylibrarytoolkit
from commandlib import python, python_bin, Command, CommandError
from hitchstory import StoryCollection
from pathquery import pathquery
from path import Path
from os import getenv


class Directories:
    gen = Path("/gen")
    key = Path("/src/hitch/")
    project = Path("/src/")
    share = Path("/gen")


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


class ProjectToolkitV2(ProjectToolkit):
    def __init__(self, name, slug, github_address, image=""):
        self._name = name
        self._project_name = slug
        self._github_address = github_address
        self.DIR = Directories()
        self._path = self.DIR
        self._image = image

    def devenv(self):
        env = pyenv.DevelopmentVirtualenv(
            pyenv.Pyenv(self.DIR.gen / "pyenv"),
            self.DIR.project.joinpath("hitch", "devenv.yml"),
            self.DIR.project.joinpath("hitch", "debugrequirements.txt"),
            self.DIR.project,
            self.DIR.project.joinpath("pyproject.toml").text(),
        )
        env.ensure_built()
        return env

    def deploy(self, testpypi=False):
        relenv = pyenv.ReleaseVirtualenv(pyenv.Pyenv(self.DIR.gen / "pyenv"))
        relenv.ensure_built()

        hitchpylibrarytoolkit.deploy.deploy(
            self._project_name,
            self._github_address,
            self.DIR.gen,
            testpypi=testpypi,
            dryrun=False,
            python_cmd=Command(relenv.python_path),
        )

    def package_test(self):
        relenv = pyenv.ReleaseVirtualenv(pyenv.Pyenv(self.DIR.gen / "pyenv"))
        relenv.ensure_built()

        hitchpylibrarytoolkit.deploy.deploy(
            self._project_name,
            self._github_address,
            self.DIR.gen,
            testpypi=True,
            dryrun=True,
            python_cmd=Command(relenv.python_path),
        )

    def draft_docs(self, storybook):
        ProjectDocumentation(
            storybook,
            self.DIR.project,
            self.DIR.project / "docs" / "draft",
            self._name,
            self._github_address,
            image=self._image,
        ).generate()

    def publish(self, storybook):
        if self.DIR.gen.joinpath(self._project_name).exists():
            self.DIR.gen.joinpath(self._project_name).rmtree()

        Path("/root/.ssh/known_hosts").write_text(
            Command("ssh-keyscan", "github.com").output()
        )

        print(getenv("CI"))
        if getenv("CI").lower() == "true":
            Command(
                "git",
                "clone",
                "https://{}@github.com/{}.git".format(
                    getenv("GITHUBTOKEN").rstrip(),
                    self._github_address,
                ),
            ).in_dir(self.DIR.gen).run()
        else:
            Command(
                "git", "clone", "git@github.com:{}.git".format(self._github_address)
            ).in_dir(self.DIR.gen).run()

        git = Command("git").in_dir(self.DIR.gen / self._project_name)
        git("config", "user.name", "Bot").run()
        git("config", "user.email", "bot@hitchdev.com").run()
        git("rm", "-r", "docs/public").run()

        ProjectDocumentation(
            storybook,
            self.DIR.project,
            self.DIR.gen / self._project_name / "docs" / "public",
            self._name,
            self._github_address,
            image=self._image,
        ).generate()

        ProjectDocumentation(
            storybook,
            self.DIR.project,
            self.DIR.gen / self._project_name / "docs" / "draft",
            self._name,
            self._github_address,
            image="",
        ).generate(readme=True)
        
        import re
        text_with_absolute_links = re.sub(
            r"(\[.*?\])\(((?!http).*?)\)",
            r"\g<1>(https://hitchdev.com/{0}/\g<2>)".format(self._project_name),
            self.DIR.gen.joinpath(self._project_name, "docs", "draft", "index.md").text()
        ).replace("\r\n", "\n")

        self.DIR.gen.joinpath(self._project_name, "README.md").write_text(
            text_with_absolute_links
        )
        self.DIR.gen.joinpath(self._project_name, "docs", "draft", "changelog.md").copy(
            self.DIR.gen / self._project_name / "CHANGELOG.md"
        )

        git("add", self.DIR.gen / self._project_name).run()
        git("commit", "-m", "DOCS : Regenerated docs.").in_dir(
            self.DIR.gen / self._project_name
        ).run()

        if getenv("CI").lower() == "true":
            import stat
            import os

            git(
                "config",
                "credential.https://github.com.username",
                getenv("GITHUBTOKEN").rstrip(),
            ).run()
            Path("/gen/askpass.sh").write_text(
                "echo {}".format(getenv("GITHUBTOKEN").rstrip())
            )

            st = os.stat("/gen/askpass.sh")
            os.chmod("/gen/askpass.sh", st.st_mode | stat.S_IEXEC)
            git("push").with_env(GIT_ASKPASS="/gen/askpass.sh").run()
        else:
            git("push").run()
