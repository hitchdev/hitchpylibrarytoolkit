from commandlib import python, python_bin


def reformat(project_dir, project_name):
    python_bin.black(project_dir / project_name).run()
    python_bin.black(project_dir / "hitch" / "key.py").run()
    python("-m", "flake8")(
        DIR.project.joinpath(project_name),
        "--max-line-length=100",
        "--exclude=__init__.py",
    ).run()
    python("-m", "flake8")(
        project_dir.joinpath("hitch", "key.py"),
        "--max-line-length=100",
        "--exclude=__init__.py",
    ).run()
    print("Reformat / lint success")
3
