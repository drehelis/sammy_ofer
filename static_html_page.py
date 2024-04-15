from jinja2 import Environment, FileSystemLoader
from random import choice
from pathlib import Path
from shutil import copy
import datetime

from git import Repo
from logger import logger

REPO_URL = "https://github.com/drehelis/sammy_ofer"
TMP_REPO_DIR = "/tmp/sammy_ofer"
STATIC_HTML_FILENAME = "static.html"


def gen_static_page(obj):
    environment = Environment(loader=FileSystemLoader("assets/templates"))
    template = environment.get_template("static_page.jinja2")

    content = template.render(games=obj)

    try:
        with open(STATIC_HTML_FILENAME, mode="r", encoding="utf-8") as f:
            existing_content = f.read()
    except FileNotFoundError:
        existing_content = None

    if existing_content == content:
        return

    with open(STATIC_HTML_FILENAME, mode="w", encoding="utf-8") as f:
        f.write(content)
        logger.info(f"Generated {STATIC_HTML_FILENAME} from template")

        git_commit()


def git_commit():
    try:
        repo = Repo(TMP_REPO_DIR)
        repo.remotes.origin.pull("master")
    except:
        repo = Repo.clone_from(REPO_URL, TMP_REPO_DIR)
    try:
        repo.git.checkout("static_page")
    except:
        repo.git.checkout(b="static_page")

    src = Path(__file__).resolve().parent / STATIC_HTML_FILENAME
    copy(src, f"{TMP_REPO_DIR}/{STATIC_HTML_FILENAME}")

    repo.index.add([STATIC_HTML_FILENAME])
    if not repo.index.diff("HEAD"):
        logger.info(f"{STATIC_HTML_FILENAME} is up to date")
        return

    logger.info(f"{STATIC_HTML_FILENAME} pushed to repo")
    repo.index.commit(str(datetime.datetime.now()))
    repo.git.push("--force")
    repo.git.reset("--hard", "origin/master")
