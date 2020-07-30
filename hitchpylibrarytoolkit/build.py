import hitchbuildpy


def project_build(project_name, paths, python_version, libraries=None):
    pylibrary = hitchbuildpy.VirtualenvBuild(
        base_python=hitchbuildpy.PyenvBuild(
            paths.share / "python{}".format(python_version), python_version
        ),
    ).with_requirementstxt(paths.key / "debugrequirements.txt")

    if libraries is not None:
        for library_name, library_version in libraries.items():
            pylibrary = pylibrary.with_packages(
                "{0}=={1}".format(library_name, library_version)
            )

    pylibrary.ensure_built()
    return pylibrary
