# ---------------------------------------------------------------------------------------
# CONFIG     --------------------------------------------------------------------------
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
    """wrap name in single quotes as otherwise names with spaces etc will break it"""
    return f"'{name}'"

def append(path, text):
    """append text to a file with new lines separation"""
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")