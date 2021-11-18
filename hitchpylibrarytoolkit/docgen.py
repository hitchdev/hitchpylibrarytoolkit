import dirtemplate
from hitchpylibrarytoolkit.exceptions import ToolkitError
from strictyaml import load
from git import Repo
import jinja2
from collections import OrderedDict
from templex import Templex
from pathquery import pathquery
from path import Path
import difflib
import mimetypes

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
        dirtemplate.DirTemplate(project_dir / "docs" / "src", build_dir)
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


def docgen(all_stories, project_dir, story_dir, build_dir, temp_dir, check=False):
    """
    Generate markdown documentation.
    """

    docfolder = build_dir
    if check:
        if temp_dir.exists():
            temp_dir.rmtree(ignore_errors=True)
        temp_dir.mkdir()

        directory_template(
            all_stories, project_dir, story_dir, temp_dir, readme=False
        ).ensure_built()
        temp_dir.joinpath("changelog.md").write_text(changelog(project_dir))
        temp_dir.joinpath("fingerprint.txt").remove()
        print("Docs checked")
        
        assert len(list(pathquery(temp_dir))) == len(list(pathquery(docfolder))), \
            "Different real docs to generated"
        
        for temp_docfile in pathquery(temp_dir):
            if not temp_docfile.isdir():
                equivalent_realdocfile = Path(temp_docfile.replace(temp_dir, docfolder))
                print("Checking {}".format(equivalent_realdocfile))
                textfile = mimetypes.guess_type(temp_docfile)[0] is not None and mimetypes.guess_type(temp_docfile)[0].startswith("text")
                
                if textfile:
                    error_message = "Generated file different from real,\n{}".format(''.join(difflib.ndiff(
                        equivalent_realdocfile.text().splitlines(1),
                        temp_docfile.text().splitlines(1),
                    )))
                    assert equivalent_realdocfile.text() == temp_docfile.text(), error_message
                else:
                    assert equivalent_realdocfile.bytes() == temp_docfile.bytes(), \
                        "Generated file different from real, please rerun docgen or report bug."
    else:
        if docfolder.exists():
            docfolder.rmtree(ignore_errors=True)
        docfolder.mkdir()
    
        directory_template(
            all_stories, project_dir, story_dir, docfolder, readme=False
        ).ensure_built()
        docfolder.joinpath("changelog.md").write_text(changelog(project_dir))
        docfolder.joinpath("fingerprint.txt").remove()
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
        Templex(changelog(project_dir)).assert_match(project_dir.joinpath("CHANGELOG.md").read_text())
        Templex(text_with_absolute_links).assert_match(project_dir.joinpath("README.md").read_text())
        print("README and CHANGELOG are correct.")
    else:
        project_dir.joinpath("CHANGELOG.md").write_text(changelog(project_dir))
        project_dir.joinpath("README.md").write_text(text_with_absolute_links)
        print("README and CHANGELOG generated")
