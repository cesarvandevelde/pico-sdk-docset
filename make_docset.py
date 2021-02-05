import subprocess
import shutil
from pathlib import Path


ROOT_DIR = Path(__file__).parent
HTML_DIR = ROOT_DIR / "html"
DOCSET_DIR = ROOT_DIR / "Pico SDK.docset"
DOCSET_CONTENTS_DIR = DOCSET_DIR / "Contents"
DOCSET_RESOURCES_DIR = DOCSET_CONTENTS_DIR / "Resources"
DOCSET_DOCUMENTS_DIR = DOCSET_RESOURCES_DIR / "Documents"


class DocsetException(RuntimeError):
    pass


def check_dependencies():
    print("Checking for doxygen and docsetutil")
    result = subprocess.run(["which", "doxygen"], capture_output=True)

    if not result.stdout:
        raise DocsetException("Doxygen not found!")

    result = subprocess.run(["which", "docsetutil"], capture_output=True)

    if not result.stdout:
        raise DocsetException("Docsetutil not found!")


def run_doxygen():
    try:
        subprocess.run(["doxygen"], cwd=ROOT_DIR, check=True)
    except subprocess.CalledProcessError as e:
        raise DocsetException("Doxygen failed to generate HTML files") from e


def create_dirs():
    dirs_to_create = [
        DOCSET_DIR,
        DOCSET_CONTENTS_DIR,
        DOCSET_RESOURCES_DIR,
        DOCSET_DOCUMENTS_DIR
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(exist_ok=True)


def copy_files():
    ignore = shutil.ignore_patterns(
        "*.docset",
        "Nodes.xml",
        "Tokens.xml",
        "Info.plist",
        "Makefile"
    )

    shutil.copytree(
        HTML_DIR,
        DOCSET_DOCUMENTS_DIR,
        ignore=ignore,
        dirs_exist_ok=True
    )

    shutil.copy(HTML_DIR / "Nodes.xml", DOCSET_RESOURCES_DIR)
    shutil.copy(HTML_DIR / "Tokens.xml", DOCSET_RESOURCES_DIR)
    shutil.copy(ROOT_DIR / "overrides" /"Info.plist", DOCSET_CONTENTS_DIR)
    shutil.copy(ROOT_DIR / "overrides" /"icon.png", DOCSET_DIR)


def build_index():
    try:
        subprocess.run(
            ["docsetutil", "index", str(DOCSET_DIR.relative_to(ROOT_DIR))],
            cwd=ROOT_DIR,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise DocsetException("Failed to build docset index") from e


def make_docset():
    check_dependencies()
    run_doxygen()
    create_dirs()
    copy_files()
    build_index()


if __name__ == "__main__":
    try:
        make_docset()
    except DocsetException as e:
        print(e)
        print("Aborting...")
        exit(-1)
    else:
        print("Presto!")
        print(F"Docset can be found at {DOCSET_DIR}")
