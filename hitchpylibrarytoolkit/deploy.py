from commandlib import Command, python
from path import Path
import os


def deploy(project_name, github_path, temp_path, testpypi=False, dryrun=False):
    git = Command("git")

    if temp_path.joinpath(project_name).exists():
        temp_path.joinpath(project_name).rmtree()

    Path("/root/.ssh/known_hosts").write_text(
        Command("ssh-keyscan", "github.com").output()
    )

    git("clone", "git@github.com:{}.git".format(github_path)).in_dir(temp_path).run()
    project = temp_path / project_name
    version = project.joinpath("VERSION").text().rstrip()
    initpy = project.joinpath(project_name, "__init__.py")
    original_initpy_contents = initpy.bytes().decode("utf8")
    initpy.write_text(original_initpy_contents.replace("DEVELOPMENT_VERSION", version))
    python("-m", "pip", "wheel", ".", "-w", "dist").in_dir(project).run()
    python("-m", "build", "--sdist").in_dir(project).run()
    initpy.write_text(original_initpy_contents)

    # Upload to pypi
    wheel_args = ["-m", "twine", "upload"]
    if testpypi:
        wheel_args += ["--repository", "testpypi"]
    wheel_args += ["dist/{}-{}-py3-none-any.whl".format(project_name, version)]

    if not dryrun:
        python(*wheel_args).in_dir(project).with_env(
            TWINE_USERNAME="__token__",
            TWINE_PASSWORD=os.getenv("PYPITOKEN"),
        ).run()

    sdist_args = ["-m", "twine", "upload"]
    if testpypi:
        sdist_args += ["--repository", "testpypi"]
    sdist_args += ["dist/{0}-{1}.tar.gz".format(project_name, version)]
    
    if not dryrun:
        python(*sdist_args).in_dir(project).with_env(
            TWINE_USERNAME="__token__",
            TWINE_PASSWORD=os.getenv("PYPITOKEN"),
        ).run()

    # Clean up
    temp_path.joinpath(project_name).rmtree()
