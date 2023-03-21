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


toolkit = hitchpylibrarytoolkit.ProjectToolkitV2(
    "HitchPyLibraryToolkit",
    "hitchpylibrarytoolkit",
    "hitchdev/hitchpylibrarytoolkit",
)


@group(invoke_without_command=True)
@pass_context
def cli(ctx):
    """Integration test command line interface."""
    pass


@cli.command()
def deploy():
    """
    Deploy to pypi as specified version.
    """
    hitchpylibrarytoolkit.deploy.deploy(
        PROJECT_NAME,
        "hitchdev/hitchpylibrarytoolkit",
        DIR.gen,
        testpypi=False,
    )



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
    

@cli.command()
def build():
    pass


if __name__ == "__main__":
    cli()
