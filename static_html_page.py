import datetime
import os
from pathlib import Path
from shutil import copy, copytree, rmtree

from git import Repo, exc
from jinja2 import Environment, FileSystemLoader

import jinja_filters as jf
from logger import logger

REPO_URL = f"https://{os.getenv('GH_PAT')}@github.com/drehelis/sammy_ofer"
TMP_REPO_DIR = "/tmp/sammy_ofer"
GH_PAGES_BRANCH = "static_page"

PATHS_TO_SYNC = [
    "static.html",
    "rem.html",
    "assets/teams"
]

absolute_path = Path(__file__).resolve().parent


def gen_static_page(db_data):
    upcoming, _ = db_data

    env = Environment(loader=FileSystemLoader(absolute_path / "assets/templates/"))
    env.filters["babel_format_full_heb"] = jf.babel_format_full_heb
    
    pages_to_generate = {
        "static.html": "static_page.jinja2",
        "rem.html": "reminder.jinja2"
    }

    rendered_contents = {}
    any_changed = False

    for filename, template_name in pages_to_generate.items():
        content = env.get_template(template_name).render(upcoming=upcoming, datetime=datetime)
        rendered_contents[filename] = content
        
        file_path = absolute_path / filename
        if not file_path.exists() or file_path.read_text(encoding="utf-8") != content:
            any_changed = True

    if not any_changed:
        return

    for filename, content in rendered_contents.items():
        (absolute_path / filename).write_text(content, encoding="utf-8")
        logger.info(f"Generated {filename}")

    if os.getenv("SKIP_COMMIT"):
        logger.info("SKIP_COMMIT is set, skipping git commit")
        return

    git_commit()


def _get_or_init_repo() -> Repo:
    try:
        repo = Repo(TMP_REPO_DIR)
        logger.debug(f"Using existing repo at {TMP_REPO_DIR}")
        repo.remotes.origin.pull(GH_PAGES_BRANCH)
    except (exc.NoSuchPathError, exc.InvalidGitRepositoryError):
        logger.info(f"Cloning repo from {REPO_URL} to {TMP_REPO_DIR}")
        repo = Repo.clone_from(REPO_URL, TMP_REPO_DIR)

    repo.config_writer().set_value("user", "name", "sammy-ofer-bot").release()
    repo.config_writer().set_value("user", "email", "sammy-ofer-bot@mail.com").release()

    try:
        repo.git.checkout(GH_PAGES_BRANCH)
    except exc.GitCommandError:
        logger.info(f"Checkout branch: {GH_PAGES_BRANCH}")
        repo.git.checkout(b=GH_PAGES_BRANCH)
    
    return repo


def _sync_files_to_repo(repo_path: Path):
    for path_str in PATHS_TO_SYNC:
        src = absolute_path / path_str
        dst = repo_path / path_str
        
        if not src.exists():
            logger.warning(f"Path does not exist: {src}")
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)

        if not src.is_dir():
            copy(src, dst)
            logger.debug(f"Synced file: {path_str}")
            continue

        if dst.exists():
            rmtree(dst)
        copytree(src, dst)
        logger.debug(f"Synced directory: {path_str}")


def git_commit():
    try:
        repo = _get_or_init_repo()
        repo_path = Path(repo.working_dir)

        _sync_files_to_repo(repo_path)

        repo.index.add(PATHS_TO_SYNC)

        if not repo.index.diff("HEAD"):
            logger.info("No changes detected; repository is up to date.")
            return

        commit_msg = f"Auto-update: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        repo.index.commit(commit_msg)
        repo.git.push()
        
        logger.info(f"Successfully pushed updates to GitHub branch: {GH_PAGES_BRANCH}")

    except Exception as e:
        logger.error(f"Failed to sync with GitHub: {str(e)}", exc_info=True)
