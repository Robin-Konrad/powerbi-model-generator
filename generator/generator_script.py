
"""
Overview:
    script takes a pbip project and a tablename,
    and generates _globals, date granularity parameter, relationships, measures and columns

    this script assumes that _DateTable, _DateGranularity already exists   (as in sample template .pbip)

Instructions:
    -start up a new emtpy sample template .pbip and import the table you want
    -set up config below with the project and the table names
    -run script  (with script in same dir as the pbip files)

    at the end in main() simply comment out any generator funcs you do not want to run
"""

import os
from core import *
from measures_columns import add_fixed_measures_columns
from globals_table import create_globals_table
from granularity_parameter import create_date_granularity_parameter

# creating relationship  -----------------------------------------
def add_date_relationship():
    """create relationship between date table date and specified date field"""
    relationship_name = f"{TABLE_NAME}-Date"
    text = (
        f"relationship {quote(relationship_name)}\n"
        f"\tfromColumn: {quote(TABLE_NAME)}.{quote(DATE_FIELD_NAME)}\n"
        f"\ttoColumn: _DateTable.Date"
    )
    append(RELATIONSHIPS_FILE, text)


# RUNNING--------------------------
# comment out parts if not needed--------------------------------------

def main():

    if not os.path.exists(TABLE_FILE):
        raise FileNotFoundError(
            f"{TABLE_FILE} not found check that TABLE_NAME is set to correct value in config "
        )

    create_date_granularity_parameter()
    create_globals_table()
    add_date_relationship()
    add_fixed_measures_columns()

    print(f"Done. Review {TABLE_FILE} and {RELATIONSHIPS_FILE}, then open the .pbip in Desktop.")


if __name__ == "__main__":
    main()