from pathlib import Path
import re

import generator.core as core

OBJECT_KEYWORDS = ("table", "column", "measure")

# each keyword layer depth and its common keywords
LAYER_KEYWORDS = {
    0: ["table"],
    1: ["column", "measure", "partition"],
    2: ["dataType", "formatString", "summarizeBy", "isNameInferred",
        "sourceColumn", "dataCategory"],
}

KEYWORD_TO_LAYER = {}
for layer, keywords in LAYER_KEYWORDS.items():
    for keyword in keywords:
        KEYWORD_TO_LAYER[keyword] = layer


def normalize_indentation(text):
    """
        Converts all tabs to 4 spaces.

        :param text:      str, required      the file's text
        :return:          str                normalized text
    """
    return text.replace("\t", " " * 4)


def depth(line):
    """
        Finds the indentation depth of a line assuming 4-space indentation.

        :param line:         str, required   the line to be checked
        :return:             int             the indentation depth
    """
    leading_spaces = len(line) - len(line.lstrip(" "))
    return leading_spaces // 4

def check_layered_indentation(text, filename):
    """
        Checks if each keyword line's indentation depth is correct based on tmdl rules.

        :param text:         str, required   normalized file text
        :param filename:     str, required   the file's name
        :return:             list[str]       list of error messages
    """
    errors = []
    keywords = tuple(KEYWORD_TO_LAYER.keys())

    for i, line in enumerate(text.split("\n"), start=1):
        stripped = line.strip()
        if not stripped:
            continue

        match = re.match(r"([A-Za-z]+)", stripped)    # get first word in line
        if not match:
            continue

        keyword = match.group(1)
        if keyword not in KEYWORD_TO_LAYER:
            continue

        expected_depth = KEYWORD_TO_LAYER[keyword]
        actual_depth = depth(line)

        if actual_depth != expected_depth:
            errors.append(
                f"{filename}: line {i}: '{keyword}' expected at indentation depth {expected_depth} "
                f"found at depth {actual_depth}"
            )

    return errors


def check_quoting(text, filename):
    """
        Checks if object names that have spaces/symbols are quoted.

        :param text:         str, required   normalized file text
        :param filename:     str, required   the file's name for error reporting
        :return:             list[str]       list of error messages
    """
    errors = []

    for i, line in enumerate(text.splitlines(), start=1):
        for object_word in OBJECT_KEYWORDS:
            match = re.match(rf"\s*{object_word}\b\s+([^\s]+)", line)
            if not match:
                continue

            name = match.group(1)

            has_space_or_symbol = not re.match(r"^[A-Za-z0-9_.'-]+$", name)
            is_quoted = name.startswith("'") and name.endswith("'")

            if has_space_or_symbol and not is_quoted:
                errors.append(
                    f"{filename}: line {i}: unquoted {object_word} name '{name}' contains a space or symbol"
                )

    return errors


def lint_file(path: Path):
    """
        Runs lint checks on a .tmdl file.

        :param path:         Path, required   the file path
        :return:             list[str]        list of error messages
    """
    original_text = path.read_text(encoding="utf-8")
    normalized = normalize_indentation(original_text)
    filename = path.name

    return (
        check_layered_indentation(normalized, filename)
        + check_quoting(normalized, filename)
    )


def lint_run():
    """
        Runs lint checks on required .tmdl files: _DateTable, _DateGranularity, _Globals, and the fact table.

        :return:            list[str]   list of all error messages found
    """
    errors = []
    tables_dir = Path(core.TABLES_DIR)

    required_files = [
        tables_dir / "_DateTable.tmdl",
        tables_dir / "_DateGranularity.tmdl",
        tables_dir / "_Globals.tmdl",
        Path(core.TABLE_FILE)            # fact table
    ]

    for path in required_files:
        if path.exists():
            errors.extend(lint_file(path))

    return errors


if __name__ == "__main__":
    problems = lint_run()

    if problems:
        print(f"Found {len(problems)} issue(s):")
        for p in problems:
            print(f" - {p}")
        raise SystemExit(1)

    print("tmdl_lint found no issues.")
    raise SystemExit(0)
