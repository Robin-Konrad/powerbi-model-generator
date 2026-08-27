import json

with open("../config.json") as f:
    _cfg = json.load(f)

PROJECTNAME = _cfg["project_name"]
TABLE_NAME = _cfg["table_name"]
DATE_FIELD_NAME = _cfg["date_field_name"]
GRANULARITY_ALL = _cfg["granularity_all"]
ACADEMIC_MONTH = _cfg["academic_month"]

TABLES_DIR = f"../template/{PROJECTNAME}.SemanticModel/definition/tables"
RELATIONSHIPS_FILE = f"../template/{PROJECTNAME}.SemanticModel/definition/relationships.tmdl"
TABLE_FILE = f"{TABLES_DIR}/{TABLE_NAME}.tmdl"

# helper functions
def quote(name):
    """
    Wraps a name string in single quotes so it's always a valid identifier in tmdl, as it's required
    for column/measure names containing spaces or special characters.

    :param name:        str, required        name of a column or measure
    :return:            str                  name param wrapped inside single quotes
    """
    return f"'{name}'"

def append(path, text):
    """
    Appends text to a file followed by a newline.

    :param path:        str, required        path of the file to append to
    :param text:        str, required        the text that will be appended
    :return:            None
    """
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")