import subprocess
import shutil
import sqlite3
import re
from urllib.parse import quote as url_escape
from pathlib import Path


ROOT_DIR = Path(__file__).parent
HTML_DIR = ROOT_DIR / "html"
DOCSET_DIR = ROOT_DIR / "Raspberry Pi Pico SDK.docset"
DOCSET_CONTENTS_DIR = DOCSET_DIR / "Contents"
DOCSET_RESOURCES_DIR = DOCSET_CONTENTS_DIR / "Resources"
DOCSET_DOCUMENTS_DIR = DOCSET_RESOURCES_DIR / "Documents"
DB_PATH = DOCSET_RESOURCES_DIR / "docSet.dsidx"
ARCHIVE_PATH = ROOT_DIR / "Raspberry_Pi_Pico_SDK.tgz"

TOKEN_QUERY = """
SELECT
    meta.ZANCHOR as anchor,
    tokentype.ZTYPENAME as entry_type,
    token.ZTOKENNAME as entry_name
FROM
    ZTOKENMETAINFORMATION meta
    INNER JOIN ZTOKEN token ON meta.ZTOKEN = token.Z_PK
    INNER JOIN ZTOKENTYPE tokentype on token.ZTOKENTYPE = tokentype.Z_PK
WHERE
    meta.ZANCHOR IN ({seq})
"""

ANCHOR_RE = re.compile(r"""<a id="(ga[a-z0-9]{32})"><\/a>""")


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


def lookup_tokens(conn, uuids):
    seq = ", ".join("?" for _ in uuids)
    query_seq = TOKEN_QUERY.format(seq=seq)

    tokens = {}

    cur = conn.cursor()

    for row in cur.execute(query_seq, uuids):
        tokens[row[0]] = (row[1], row[2])

    return tokens


def add_toc_to_file(conn, html_path):
    with open(html_path, "r") as f:
        html = f.read()

    uuids = []

    for match in ANCHOR_RE.finditer(html):
        uuids.append(match.group(1))

    if not uuids:
        # Nothing to do, leave file as-is
        return

    tokens = lookup_tokens(conn, uuids)

    def add_anchor(match):
        uuid = match.group(1)

        if uuid not in tokens:
            return match.group(0)

        original = match.group(0)
        entry_type = tokens[uuid][0]
        entry_name = url_escape(tokens[uuid][1])

        anchor_name = f"//apple_ref/cpp/{entry_type}/{entry_name}"

        return f"{original}<a name=\"{anchor_name}\" class=\"dashAnchor\"></a>"

    html = ANCHOR_RE.sub(add_anchor, html)

    with open(html_path, "w") as f:
        f.write(html)


def add_tocs():
    conn = sqlite3.connect(f"file://{DB_PATH}?mode=ro", uri=True)

    for html_path in DOCSET_DOCUMENTS_DIR.glob("*.html"):
        add_toc_to_file(conn, html_path)

    conn.close()


def make_archive():
    archive_rel = ARCHIVE_PATH.relative_to(ROOT_DIR)
    docset_rel = DOCSET_DIR.relative_to(ROOT_DIR)

    subprocess.run(
        ["tar", "--exclude=\'.DS_Store\'", "-cvzf", archive_rel, docset_rel],
        cwd=ROOT_DIR
    )


def make_docset():
    check_dependencies()
    run_doxygen()
    create_dirs()
    copy_files()
    build_index()
    add_tocs()
    make_archive()


if __name__ == "__main__":
    try:
        make_docset()
    except DocsetException as e:
        print(e)
        print("Aborting...")
        exit(-1)
    else:
        print("Presto!")
        print(f"Docset can be found at {DOCSET_DIR}")
