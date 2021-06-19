from commandlib import python, python_bin

def reformat(project_dir, project_name):
    python_bin.black(project_dir / project_name).run()
    python_bin.black(project_dir / "hitch" / "key.py").run()
    print("Reformat success")
    lint(project_dir, project_name)
