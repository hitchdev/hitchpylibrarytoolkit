import dirtemplate
from strictyaml import load


def title(dirfile):
    assert len(dirfile.text().split("---")) >= 3, "{} doesn't have ---".format(
        dirfile
    )
    return load(dirfile.text().split("---")[1]).data.get("title", "misc")


def docgen(all_stories, project_dir, story_dir, build_dir):
    """
    Generate markdown documentation.
    """

    docfolder = build_dir / "docs"
    if docfolder.exists():
        docfolder.rmtree(ignore_errors=True)
    docfolder.mkdir()

    template = (
        dirtemplate.DirTemplate("docs", project_dir / "docs", build_dir)
        .with_files(
            template_story_jinja2={
                "using/alpha/{0}.md".format(story.info["docs"]): {"story": story}
                for story in all_stories.ordered_by_name()
                if story.info.get("docs") is not None
            }
        )
        .with_vars(
            readme=False,
            quickstart=all_stories.in_filename(story_dir / "quickstart.story")
            .non_variations()
            .ordered_by_file(),
            include_title=True,
        )
        .with_functions(title=title)
    )
    template.ensure_built()
    print("Docs generated")


def readmegen(all_stories, project_dir, story_dir, build_dir, project_name):
    docfolder = build_dir / "readme"
    if docfolder.exists():
        docfolder.rmtree(ignore_errors=True)
    docfolder.mkdir()

    template = (
        dirtemplate.DirTemplate("readme", project_dir / "docs", build_dir)
        .with_files(
            template_story_jinja2={
                "using/alpha/{0}.md".format(story.info["docs"]): {"story": story}
                for story in all_stories.ordered_by_name()
                if story.info.get("docs") is not None
            }
        )
        .with_vars(
            readme=True,
            quickstart=all_stories.in_filename(story_dir / "quickstart.story")
            .non_variations()
            .ordered_by_file(),
        )
        .with_functions(title=title)
    )
    template.ensure_built()

    readme_text = docfolder.joinpath("index.md").text()

    import re

    text_with_absolute_links = re.sub(
        r"(\[.*?\])\(((?!http).*?)\)",
        "\g<1>(https://hitchdev.com/{0}/\g<2>)".format(project_name),
        readme_text
    )

    project_dir.joinpath("README.md").write_text(text_with_absolute_links)
    print("README generated")
