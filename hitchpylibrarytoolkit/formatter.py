from commandlib import python, python_bin


def lint(project_dir, project_name):
    python("-m", "flake8")(
        project_dir.joinpath(project_name),
        "--max-line-length=100",
        "--exclude=__init__.py",
    ).run()
    python("-m", "flake8")(
        project_dir.joinpath("hitch", "key.py"),
        "--max-line-length=100",
        "--exclude=__init__.py",
    ).run()


def reformat(project_dir, project_name):
    python_bin.black(project_dir / project_name).run()
    python_bin.black(project_dir / "hitch" / "key.py").run()
    print("Reformat success")
    lint(project_dir, project_name)
