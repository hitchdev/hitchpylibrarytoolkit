from commandlib import Command, python


def deploy(project_path, name, version):
    git = Command("git").in_dir(project_path)
    version_file = project_path.joinpath("VERSION")
    old_version = version_file.bytes().decode("utf8")
    if version_file.bytes().decode("utf8") != version:
        project_path.joinpath("VERSION").write_text(version)
        git("add", "VERSION").run()
        git(
            "commit", "-m", "RELEASE: Version {0} -> {1}".format(old_version, version)
        ).run()
        git("push").run()
        git("tag", "-a", version, "-m", "Version {0}".format(version)).run()
        git("push", "origin", version).run()
    else:
        git("push").run()

    # Set __version__ variable in __init__.py, build sdist and put it back
    initpy = project_path.joinpath(name, "__init__.py")
    original_initpy_contents = initpy.bytes().decode("utf8")
    initpy.write_text(original_initpy_contents.replace("DEVELOPMENT_VERSION", version))
    python("setup.py", "sdist").in_dir(project_path).run()
    initpy.write_text(original_initpy_contents)

    # Upload to pypi
    python("-m", "twine", "upload", "dist/{0}-{1}.tar.gz".format(name, version)).in_dir(
        project_path
    ).run()
