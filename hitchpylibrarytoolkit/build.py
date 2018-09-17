import hitchbuildpy


def project_build(project_name, paths, python_version, libraries):
    pylibrary = hitchbuildpy.PyLibrary(
        name="py{0}".format(python_version),
        base_python=hitchbuildpy.PyenvBuild(python_version)
                                .with_build_path(paths.share),
        module_name=project_name,
        library_src=paths.project,
    ).with_requirementstxt(
        paths.key/"debugrequirements.txt"
    ).with_build_path(paths.gen)

    for library_name, library_version in libraries.items():
        pylibrary = pylibrary.with_packages(
            "{0}=={1}".format(library_name, library_version)
        )

    pylibrary.ensure_built()
    return pylibrary
