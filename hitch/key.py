import hitchpylibrarytoolkit
from click import argument, group, pass_context
from path import Path


PROJECT_NAME = "hitchpylibrarytoolkit"
GITHUB_PATH = "hitchdev/hitchpylibrarytoolkit"


class Directories:
    gen = Path("/gen")
    key = Path("/src/hitch/")
    project = Path("/src/")
    share = Path("/gen")


DIR = Directories()


toolkit = hitchpylibrarytoolkit.ProjectToolkit(
    "hitchpylibrarytoolkit",
    DIR,
)


@group(invoke_without_command=True)
@pass_context
def cli(ctx):
    """Integration test command line interface."""
    pass


@cli.command()
@argument("test", nargs=1)
def deploy(test="notest"):
    """
    Deploy to pypi as specified version.
    """
    #import IPython ; IPython.embed()
    #hitchpylibrarytoolkit.deploy.deploy(
        #PROJECT_NAME,
        #"hitchdev/hitchpylibrarytoolkit",
        #DIR.gen,
        #testpypi=False,
    #)
    
    from commandlib import python, Command

    git = Command("git")

    if DIR.gen.joinpath(PROJECT_NAME).exists():
        DIR.gen.joinpath(PROJECT_NAME).rmtree()

    git("clone", "git@github.com:{}.git".format(GITHUB_PATH)).in_dir(DIR.gen).run()
    project = DIR.gen / PROJECT_NAME
    version = project.joinpath("VERSION").text().rstrip()
    initpy = project.joinpath(PROJECT_NAME, "__init__.py")
    original_initpy_contents = initpy.bytes().decode("utf8")
    initpy.write_text(original_initpy_contents.replace("DEVELOPMENT_VERSION", version))
    python("-m", "pip", "wheel", ".", "-w", "dist").in_dir(project).run()
    python("-m", "build", "--sdist").in_dir(project).run()
    initpy.write_text(original_initpy_contents)

    # Upload to pypi
    wheel_args = ["-m", "twine", "upload"]
    if test == "test":
        wheel_args += ["--repository", "testpypi"]
    wheel_args += ["dist/{}-{}-py3-none-any.whl".format(PROJECT_NAME, version)]

    python(*wheel_args).in_dir(project).run()

    sdist_args = ["-m", "twine", "upload"]
    if test == "test":
        sdist_args += ["--repository", "testpypi"]
    sdist_args += ["dist/{0}-{1}.tar.gz".format(PROJECT_NAME, version)]
    python(*sdist_args).in_dir(project).run()

    # Clean up
    DIR.gen.joinpath(PROJECT_NAME).rmtree()


@cli.command()
def lint():
    """
    Lint the package
    """
    toolkit.lint()


@cli.command()
def reformat():
    """
    Reformat using black and then relint.
    """
    toolkit.reformat()


if __name__ == "__main__":
    cli()
