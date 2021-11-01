import dirtemplate
from hitchpylibrarytoolkit.exceptions import ToolkitError
from strictyaml import load
from git import Repo
import jinja2
from collections import OrderedDict

CHANGELOG_MD_TEMPLATE = """\
# Changelog

{% for version, changes in version_changes.items() %}
### {% if version != None %}{{ version }}{% else %}Latest{% endif %}

{% for change in changes -%}
* {{ change }}
{%- else %}
No relevant code changes.
{%- endfor %}
{% endfor %}
"""

KEYWORDS = ["FEATURE", "BUGFIX", "BUG", "MINOR", "MAJOR", "PATCH", "PERFORMANCE"]


def changelog(project_dir):
    repo = Repo(project_dir)
    tag_commits = {tag.commit: tag for tag in repo.tags}

    current_version = None
    changes = []
    version_changes = OrderedDict()

    for commit in repo.iter_commits():
        if commit in tag_commits:
            version_changes[current_version] = changes
            current_version = tag_commits[commit].name
            changes = []

        message = commit.message

        for keyword in KEYWORDS:
            if message.startswith(keyword):
                if message not in changes:  # don't add dupes
                    changes.append(message)

    return jinja2.Template(CHANGELOG_MD_TEMPLATE).render(
        version_changes=version_changes
    ).replace("\r\n", "\n")


def directory_template(all_stories, project_dir, story_dir, build_dir, readme=False):
    return (
        dirtemplate.DirTemplate(project_dir / "docs", build_dir)
        .with_files(
            template_story_jinja2={
                "using/alpha/{0}.md".format(story.info["docs"]): {"story": story}
                for story in all_stories.ordered_by_name()
                if story.info.get("docs") is not None
            }
        )
        .with_vars(
            readme=readme,
            quickstart=all_stories.in_filename(story_dir / "quickstart.story")
            .non_variations()
            .ordered_by_file(),
            include_title=True,
        )
        .with_functions(title=title)
    )


def title(dirfile):
    assert len(dirfile.text().split("---")) >= 3, "{} doesn't have ---".format(dirfile)
    return load(dirfile.text().split("---")[1]).data.get("title", "misc")


def docgen(all_stories, project_dir, story_dir, build_dir):
    """
    Generate markdown documentation.
    """

    docfolder = build_dir / "docs"
    if docfolder.exists():
        docfolder.rmtree(ignore_errors=True)
    docfolder.mkdir()

    directory_template(
        all_stories, project_dir, story_dir, docfolder, readme=False
    ).ensure_built()
    docfolder.joinpath("changelog.md").write_text(changelog(project_dir))
    print("Docs generated")


def readmegen(all_stories, project_dir, story_dir, build_dir, project_name, check=False):
    docfolder = build_dir / "readme"
    if docfolder.exists():
        docfolder.rmtree(ignore_errors=True)
    docfolder.mkdir()

    directory_template(
        all_stories, project_dir, story_dir, docfolder, readme=True
    ).ensure_built()

    import re

    text_with_absolute_links = re.sub(
        r"(\[.*?\])\(((?!http).*?)\)",
        r"\g<1>(https://hitchdev.com/{0}/\g<2>)".format(project_name),
        docfolder.joinpath("index.md").text(),
    ).replace("\r\n", "\n")

    if check:
        if changelog(project_dir) != project_dir.joinpath("CHANGELOG.md").read_text():
            raise ToolkitError("Generated CHANGELOG.md hasn't been updated. Run hk readmegen and try again.")
        if text_with_absolute_links != project_dir.joinpath("README.md").read_text():
            raise ToolkitError("Generated README.md hasn't been updated. Run hk readmegen and try again.")
        print("README and CHANGELOG are correct.")
    else:
        project_dir.joinpath("CHANGELOG.md").write_text(changelog(project_dir))
        project_dir.joinpath("README.md").write_text(text_with_absolute_links)
        print("README and CHANGELOG generated")
