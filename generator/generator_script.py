import os
import generator.core as core
from measures_columns import add_fixed_measures_columns
from globals_table import create_globals_table
from granularity_parameter import create_date_granularity_parameter
from tmdl_lint import lint_run

def add_date_relationship():
    """
    Creates a relationship between _DateTable date and the fact table's specified
    date field.

    Requires a fact table and a date field to be specified in the config file.

    :param:             None
    :return:            None
    """
    relationship_name = f"{core.TABLE_NAME}-Date"
    text = (
        f"relationship {core.quote(relationship_name)}\n"
        f"\tfromColumn: {core.quote(core.TABLE_NAME)}.{core.quote(core.DATE_FIELD_NAME)}\n"
        f"\ttoColumn: _DateTable.Date"
    )
    core.append(core.RELATIONSHIPS_FILE, text)


def main():
    """
        Runs the full generator pipeline.

        Validates the fact table exists, then generates the date granularity parameter, globals table,
        date relationship, and all the fixed measures/columns.

        :param:             None
        :return:            None
    """
    if not os.path.exists(core.TABLE_FILE):
        raise FileNotFoundError(
            f"{core.TABLE_FILE} not found check that TABLE_NAME is set to correct value in config "
        )

    create_date_granularity_parameter()
    create_globals_table()
    add_date_relationship()
    add_fixed_measures_columns()

    print(f"Script finished running. open the .pbip in Power Bi to see the results")

    # run tmdl_lint at the end to quickly find any common errors in the tmdl files
    problems = lint_run()
    if problems:
        print(f"WARNING: tmdl_lint.py found {len(problems)} issue(s):")
        for p in problems:
            print(f" - {p}")
        raise SystemExit(1)



if __name__ == "__main__":
    main()