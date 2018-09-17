import dirtemplate


def docgen(project_dir, story_dir, build_dir)
    def title(dirfile):
        assert len(dirfile.text().split("---")) >= 3, "{} doesn't have ---".format(dirfile)
        return load(dirfile.text().split("---")[1]).data.get("title", "misc")

    docfolder = build_dir / "docs"
    if docfolder.exists():
        docfolder.rmtree(ignore_errors=True)
    docfolder.mkdir()

    template = dirtemplate.DirTemplate(
        "docs", project_dir/"docs", build_dir,
    ).with_files(
        template_story_jinja2={
            "using/alpha/{0}.md".format(story.info['docs']): {"story": story}
            for story in _storybook({}).ordered_by_name()
            if story.info.get("docs") is not None
        },
    ).with_vars(
        readme=False,
        quickstart=_storybook({})
        .in_filename(story_dir/"quickstart.story")
        .non_variations()
        .ordered_by_file(),
    ).with_functions(
        title=title
    )
    template.ensure_built()
    print("Docs generated")
