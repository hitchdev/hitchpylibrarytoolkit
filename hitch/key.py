import hitchpylibrarytoolkit
from hitchrun import DIR


def deploy(version):
    """
    Deploy specified version to pypi.
    """
    hitchpylibrarytoolkit.deploy(DIR.project, "hitchpylibrarytoolkit", version)


def lint():
    """
    Lint the package
    """
    hitchpylibrarytoolkit.lint(DIR.project, "hitchpylibrarytoolkit")


def reformat():
    """
    Reformat using black and then relint.
    """
    hitchpylibrarytoolkit.reformat(DIR.project, "hitchpylibrarytoolkit")
