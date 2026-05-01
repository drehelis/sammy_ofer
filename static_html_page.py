import datetime
import os
from pathlib import Path
from shutil import copy

from git import Repo, exc
from jinja2 import Environment, FileSystemLoader

import jinja_filters as jf
from logger import logger

REPO_URL = f"https://{os.getenv('GH_PAT')}@github.com/drehelis/sammy_ofer"
TMP_REPO_DIR = "/tmp/sammy_ofer"
STATIC_HTML_FILENAME = "static.html"
REMINDER_HTML_FILENAME = "rem.html"
GH_PAGES_BRANCH = "static_page"

absolute_path = Path(__file__).resolve().parent


def gen_static_page(db_data):
    upcoming, _ = db_data

    environment = Environment(
        loader=FileSystemLoader(absolute_path / "assets/templates/")
    )
    environment.filters["babel_format_full_heb"] = jf.babel_format_full_heb
    template = environment.get_template("static_page.jinja2")

    content = template.render(upcoming=upcoming, datetime=datetime)

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

    # Generate reminder page
    reminder_template = environment.get_template("reminder.jinja2")
    reminder_content = reminder_template.render(upcoming=upcoming, datetime=datetime)
    
    with open(absolute_path / REMINDER_HTML_FILENAME, mode="w", encoding="utf-8") as f:
        f.write(reminder_content)
        logger.info(f"Generated {REMINDER_HTML_FILENAME} from template")

    if os.getenv("SKIP_COMMIT"):
        logger.info("SKIP_COMMIT is set, skipping git commit")
        return

    git_commit()


def git_commit():
    try:
        repo = Repo(TMP_REPO_DIR)
        repo.remotes.origin.pull(GH_PAGES_BRANCH)
    except (exc.NoSuchPathError, exc.InvalidGitRepositoryError):
        repo = Repo.clone_from(REPO_URL, TMP_REPO_DIR)

    repo.config_writer().set_value("user", "name", "sammy-ofer-bot").release()
    repo.config_writer().set_value("user", "email", "sammy-ofer-bot@mail.com").release()

    try:
        repo.git.checkout(GH_PAGES_BRANCH)
    except exc.GitCommandError:
        repo.git.checkout(b=GH_PAGES_BRANCH)

    src_static = absolute_path / STATIC_HTML_FILENAME
    src_reminder = absolute_path / REMINDER_HTML_FILENAME
    copy(src_static, f"{TMP_REPO_DIR}/{STATIC_HTML_FILENAME}")
    copy(src_reminder, f"{TMP_REPO_DIR}/{REMINDER_HTML_FILENAME}")

    repo.index.add([STATIC_HTML_FILENAME, REMINDER_HTML_FILENAME])
    if not repo.index.diff("HEAD"):
        logger.info("Static pages are up to date")
        return

    logger.info("Static pages pushed to repo")
    repo.index.commit(str(datetime.datetime.now()))
    repo.git.push()
