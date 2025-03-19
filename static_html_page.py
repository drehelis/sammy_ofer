import datetime
import os
from pathlib import Path
from shutil import copy

from git import Repo
from jinja2 import Environment, FileSystemLoader

import jinja_filters as jf
from logger import logger

REPO_URL = f"https://{os.getenv('GH_PAT')}@github.com/drehelis/sammy_ofer"
TMP_REPO_DIR = "/tmp/sammy_ofer"
STATIC_HTML_FILENAME = "static.html"
GH_PAGES_BRANCH = "static_page"

absolute_path = Path(__file__).resolve().parent


def gen_static_page(obj):
    environment = Environment(
        loader=FileSystemLoader(absolute_path / "assets/templates/")
    )
    environment.filters["babel_format_full_heb"] = jf.babel_format_full_heb
    template = environment.get_template("static_page.jinja2")

    content = template.render(games=obj)

    try:
        with open(
            absolute_path / STATIC_HTML_FILENAME, mode="r", encoding="utf-8"
        ) as f:
            existing_content = f.read()
    except FileNotFoundError:
        existing_content = None

    if existing_content == content:
        return

    with open(absolute_path / STATIC_HTML_FILENAME, mode="w", encoding="utf-8") as f:
        f.write(content)
        logger.info(f"Generated {STATIC_HTML_FILENAME} from template")

    if os.getenv("SKIP_COMMIT"):
        logger.info("SKIP_COMMIT is set, skipping git commit")
        return

    git_commit()


def git_commit():
    try:
        repo = Repo(TMP_REPO_DIR)
        repo.remotes.origin.pull(GH_PAGES_BRANCH)
    except:
        repo = Repo.clone_from(REPO_URL, TMP_REPO_DIR)

    repo.config_writer().set_value("user", "name", "sammy-ofer-bot").release()
    repo.config_writer().set_value("user", "email", "sammy-ofer-bot@mail.com").release()

    try:
        repo.git.checkout(GH_PAGES_BRANCH)
    except:
        repo.git.checkout(b=GH_PAGES_BRANCH)

    src = absolute_path / STATIC_HTML_FILENAME
    copy(src, f"{TMP_REPO_DIR}/{STATIC_HTML_FILENAME}")

    repo.index.add([STATIC_HTML_FILENAME])
    if not repo.index.diff("HEAD"):
        logger.info(f"{STATIC_HTML_FILENAME} is up to date")
        return

    logger.info(f"{STATIC_HTML_FILENAME} pushed to repo")
    repo.index.commit(str(datetime.datetime.now()))
    repo.git.push()
