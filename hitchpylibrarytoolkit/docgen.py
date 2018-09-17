import dirtemplate
from strictyaml import load


def docgen(all_stories, project_dir, story_dir, build_dir):
    """
    Generate markdown documentation.
    """

    def title(dirfile):
        assert len(dirfile.text().split("---")) >= 3, "{} doesn't have ---".format(
            dirfile
        )
        return load(dirfile.text().split("---")[1]).data.get("title", "misc")

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
        )
        .with_functions(title=title)
    )
    template.ensure_built()
    print("Docs generated")
