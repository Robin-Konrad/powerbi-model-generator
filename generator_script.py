
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

import re
import os


# ---------------------------------------------------------------------------------------
# CONFIG     --------------------------------------------------------------------------

PROJECTNAME = "sample_template"          # whatever is in front of .pbip in files

TABLE_NAME = "Sample Table"           # table name as it appears in the model, e.g. "Sample Table"
DATE_FIELD_NAME = "Sample Date"      # field in TABLE_NAME table that will be used as the date
GRANULARITY_ALL = True   # selector for if a 5th granularity selector All exists

TABLES_DIR = f"template/{PROJECTNAME}.SemanticModel/definition/tables"
RELATIONSHIPS_FILE = f"template/{PROJECTNAME}.SemanticModel/definition/relationships.tmdl"
TABLE_FILE = f"{TABLES_DIR}/{TABLE_NAME}.tmdl"
ACADEMIC_MONTH = 10


# ----------------------------------------------------------------------------------------
# error checking-------------------------------------------------------------------------

if not os.path.exists(TABLE_FILE):
    raise FileNotFoundError(
        f"{TABLE_FILE} not found check that TABLE_NAME is set to correct value in config "
    )



# helper functions -----------------------------------------------------------------------------

def quote(name):
    """wrap name in single quotes as otherwise names with spaces etc will break it"""
    return f"'{name}'"


def append(path, text):
    """append text to a file with new lines separation"""
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")

# creating _DateGranularity paramater
def create_date_granularity_parameter():
    items = []
    if GRANULARITY_ALL:
        items.append(("All", "Week Start"))
    items += [
        ("Month", "Month Start"),
        ("Quarter", "Year-Quarter"),
        ("Year", "Year Label"),
        ("Year (Academic)", "Year Label (Academic)"),
    ]

    item_rows = []   # get the exact row string for each item to put inside full tmdl template string
    for i, (label, col) in enumerate(items):
        item_rows.append(f'("{label}", NAMEOF({quote("_DateTable")}[{col}]), {i})')

    rows = ",\n\t\t\t\t".join(item_rows)  # add correct indentation

    template = """table _DateGranularity

    column _DateGranularity
        summarizeBy: none
        sourceColumn: [Value1]
        sortByColumn: '_DateGranularity Order'

        relatedColumnDetails
            groupByColumn: '_DateGranularity Fields'

        annotation SummarizationSetBy = Automatic

    column '_DateGranularity Fields'
        isHidden
        summarizeBy: none
        sourceColumn: [Value2]
        sortByColumn: '_DateGranularity Order'

        extendedProperty ParameterMetadata =
                {{
                  "version": 3,
                  "kind": 2
                }}

        annotation SummarizationSetBy = Automatic

    column '_DateGranularity Order'
        isHidden
        formatString: 0
        summarizeBy: sum
        sourceColumn: [Value3]

        annotation SummarizationSetBy = Automatic

    partition _DateGranularity = calculated
        mode: import
        source =
                {{
                {rows}
                }}
"""
    content = template.format(rows=rows)

    with open(f"{TABLES_DIR}/_DateGranularity.tmdl", "w", encoding="utf-8") as f:
        f.write(content)

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


# --------------------------------------------------------------------------------------------------------------
# create _Globals table and measures/columns-----------------------------------------------------------------
def create_globals_table():
    globals_file = f"{TABLES_DIR}/_Globals.tmdl"

    content = """table _Globals
    partition _Globals = calculated
    \tmode: import
    \tsource = { BLANK() }"""


    with open(globals_file, "w", encoding="utf-8") as f:
        f.write(content)

    create_globals_measures(globals_file)

def create_globals_measures(globals_file):
    append(globals_file, f"\n\tmeasure {quote('_Selected Granularity')} = SELECTEDVALUE('_DateGranularity'[_DateGranularity Order], 0)\n")
    append(globals_file, f"\tmeasure {quote('_Academic Year Month Start')} = {ACADEMIC_MONTH}\n")
    append(globals_file, f"\tmeasure {quote('_ReportingMonth')} = EOMONTH(TODAY(), -1)\n")
    append(globals_file, f"""\tmeasure {quote('Filter - Prior 25 Months')} =
        -- e.g. if current month is july 2026, returns june 2024 through june 2026
        VAR EndMonth =
            DATE(
                YEAR(EOMONTH(TODAY(), -1)),
                MONTH(EOMONTH(TODAY(), -1)),
                1
            )
        VAR StartMonth =
            EDATE(EndMonth, -24)
        VAR MonthInScope =
            MAX(_DateTable[Month Start])
        RETURN
            IF(
                MonthInScope >= StartMonth
                    && MonthInScope <= EndMonth,
                1
            )\n""")

    if GRANULARITY_ALL:
        append(globals_file, f"""\tmeasure {quote('Date (str)')} =
            SWITCH(
                [_Selected Granularity],
                0, FORMAT(FIRSTDATE('_DateTable'[Date]), "MMMM YYYY"),
                1, FORMAT(FIRSTDATE('_DateTable'[Date]), "MMMM YYYY"),
                2, "Q" & FORMAT(FIRSTDATE('_DateTable'[Date]), "Q") & " " & FORMAT(FIRSTDATE('_DateTable'[Date]), "YYYY"),
                3, FORMAT(FIRSTDATE('_DateTable'[Date]), "YYYY"),
                4, IF(
                    MONTH(FIRSTDATE('_DateTable'[Date])) >= [_Academic Year Month Start],
                    FORMAT(FIRSTDATE('_DateTable'[Date]), "YYYY") & "-" & FORMAT(EDATE(FIRSTDATE('_DateTable'[Date]), 12), "YYYY"),
                    FORMAT(EDATE(FIRSTDATE('_DateTable'[Date]), -12), "YYYY") & "-" & FORMAT(FIRSTDATE('_DateTable'[Date]), "YYYY")
                )
            )\n""")
        append(globals_file ,f"""\tmeasure {quote('_Title - Reporting Period')} =
            SWITCH(
                [_Selected Granularity],
                0, " ",
                1, "Prior Month",
                2, "QTD",
                3, "YTD",
                4, "AYTD"
            )\n""")
        append(globals_file, f"""\tmeasure {quote('_Title - Reporting Period (Delta Explainer)')} =
            SWITCH(
                [_Selected Granularity],
                0, " ",
                1, "month",
                2, "quarter",
                3, "year to date",
                4, "academic year to date"
            ) &
            " to the same " &
            SWITCH(
                [_Selected Granularity],
                0, " ",
                1, "month",
                2, "quarter",
                3, "year to date",
                4, "academic year to date"
            ) &
            " in prior year"\n""")
        append(globals_file ,f"""\tmeasure {quote('_Title - Reporting Period (Text Box Fmt)')} =
            SWITCH(
                [_Selected Granularity],
                0, " ",
                1, "Prior Month",
                2, "QTD",
                3, "YTD",
                4, "AYTD"
            )\n""")
    else:
        append(globals_file, f"""\tmeasure {quote('Date (str)')} =
            SWITCH(
                [_Selected Granularity],
                0, FORMAT(FIRSTDATE('_DateTable'[Date]), "MMMM YYYY"),
                1, "Q" & FORMAT(FIRSTDATE('_DateTable'[Date]), "Q") & " " & FORMAT(FIRSTDATE('_DateTable'[Date]), "YYYY"),
                2, FORMAT(FIRSTDATE('_DateTable'[Date]), "YYYY"),
                3, IF(
                    MONTH(FIRSTDATE('_DateTable'[Date])) >= [_Academic Year Month Start],
                    FORMAT(FIRSTDATE('_DateTable'[Date]), "YYYY") & "-" & FORMAT(EDATE(FIRSTDATE('_DateTable'[Date]), 12), "YYYY"),
                    FORMAT(EDATE(FIRSTDATE('_DateTable'[Date]), -12), "YYYY") & "-" & FORMAT(FIRSTDATE('_DateTable'[Date]), "YYYY")
                )
            )\n""")
        append(globals_file, f"""\tmeasure {quote('_Title - Reporting Period')} =
            SWITCH(
                [_Selected Granularity],
                    0, "Prior Month",
                    1, "QTD",
                    2, "YTD",
                    3, "AYTD"
                )\n""")
        append(globals_file, f"""\tmeasure {quote('_Title - Reporting Period (Delta Explainer)')} =
            SWITCH(
                [_Selected Granularity],
                0, "month",
                1, "quarter",
                2, "year to date",
                3, "academic year to date"
            ) &
            " to the same " &
            SWITCH(
                [_Selected Granularity],
                0, "month",
                1, "quarter",
                2, "year to date",
                3, "academic year to date"
            ) &
            " in prior year"\n""")
        append(globals_file, f"""\tmeasure {quote('_Title - Reporting Period (Text Box Fmt)')} =
            SWITCH(
                [_Selected Granularity],
                0, "Prior Month",
                1, "QTD",
                2, "YTD",
                3, "AYTD"
            )\n""")



# fixed columns and measures
def add_date_in_range():
    append(TABLE_FILE, f"""\tcolumn {quote('Date In Range')} =
        VAR StartDate = DATE(
            YEAR(EDATE(TODAY(), -24)),
            MONTH(EDATE(TODAY(), -24)),
            1
        )
        VAR EndDate = EOMONTH(TODAY(), 0)

        RETURN
        IF(
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] >= StartDate &&
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] <= EndDate,
            1,
            0
        )\n""")

def add_Is_Current_columns():
    append(TABLE_FILE, f"""\tcolumn {quote('_Is CAYTD')} =
        VAR ReportDate = [_ReportingMonth]
        VAR StartMonth = [_Academic Year Month Start]

        VAR AcademicYearStart =
            DATE(
                YEAR(ReportDate) - IF(MONTH(ReportDate) < StartMonth, 1, 0),
                StartMonth,
                1
            )

        RETURN
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] >= AcademicYearStart &&
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] <= ReportDate\n""")
    append(TABLE_FILE, f"""\tcolumn {quote('_Is CPM')} = 
        VAR ReportDate = EOMONTH(TODAY(), -1)
        VAR FactDate = EOMONTH('{TABLE_NAME}'[{DATE_FIELD_NAME}], 0) 

        RETURN FactDate = ReportDate\n""")
    append(TABLE_FILE, f"""\tcolumn {quote('_Is CQTD')} = 
        VAR ReportDate = [_ReportingMonth]
        VAR QuarterStart =
            DATE(
                YEAR(ReportDate),
                (QUARTER(ReportDate) - 1) * 3 + 1,
                1
            )
        RETURN
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] >= QuarterStart &&
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] <= ReportDate\n""")
    append(TABLE_FILE, f"""\tcolumn {quote('_Is CYTD')} = 
        VAR ReportDate = [_ReportingMonth]
        RETURN
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] >= DATE(YEAR(ReportDate), 1, 1) &&
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] <= ReportDate\n""")



def add_Is_Previous_columns():
    append(TABLE_FILE, f"""\tcolumn {quote('_Is PYAYTD')} =
        VAR ReportDate = [_ReportingMonth]
        VAR PYReportDate = EDATE(ReportDate, -12)

        VAR StartMonth = [_Academic Year Month Start]

        VAR AcademicYearStart =
            DATE(
                YEAR(PYReportDate) - IF(MONTH(PYReportDate) < StartMonth, 1, 0),
                StartMonth,
                1
            )

        RETURN
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] >= AcademicYearStart &&
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] <= PYReportDate\n""")

    append(TABLE_FILE, f"""\tcolumn {quote('_Is PYPM')} = 
        VAR ReportDate = [_ReportingMonth]
        VAR PYReportDate = EDATE(ReportDate, -12)

        RETURN EOMONTH('{TABLE_NAME}'[{DATE_FIELD_NAME}], 0) = EOMONTH(PYReportDate, 0)\n""")
    append(TABLE_FILE, f"""\tcolumn {quote('_Is PYQTD')} = 
        VAR ReportDate = [_ReportingMonth]
        VAR PYReportDate = EDATE(ReportDate, -12)

        VAR QuarterStart =
            DATE(
                YEAR(PYReportDate),
                (QUARTER(PYReportDate) - 1) * 3 + 1,
                1
            )

        RETURN
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] >= QuarterStart &&
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] <= PYReportDate\n""")
    append(TABLE_FILE, f"""\tcolumn {quote('_Is PYYTD')} = 
        VAR ReportDate = [_ReportingMonth]
        VAR PYReportDate = EDATE(ReportDate, -12)

        RETURN
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] >= DATE(YEAR(PYReportDate), 1, 1) &&
            '{TABLE_NAME}'[{DATE_FIELD_NAME}] <= PYReportDate\n""")


# ---------------------------------------------------------------------------
# per-numeric-field measures: rename to (No Agg), add Sum + period measures


NUMERIC_TYPES = ("int64", "double", "decimal")

def find_numeric_columns():
    """scans table file for `column X` blocks with a numeric dataType."""
    text = open(TABLE_FILE).read()
    pattern = r"\tcolumn (?:'([^']+)'|(\S+))\n\t\tdataType: (?:" + "|".join(NUMERIC_TYPES) + ")"
    return [quoted or plain for quoted, plain, *_ in re.findall(pattern, text)]


def rename_to_no_agg(field):
    """rename column to  from 'field' to 'field (No Agg)', keeping sourceColumn pointed
    at the original power query field."""
    text = open(TABLE_FILE, encoding="utf-8").read()

    quoted_old = f"\tcolumn {quote(field)}"
    plain_old = f"\tcolumn {field}"

    if quoted_old in text:
        old = quoted_old
    elif plain_old in text:
        old = plain_old
    else:
        raise ValueError(f"Column '{field}' not found in {TABLE_FILE}")

    # find this column's block: from the header line up to the next
    # top-level column/measure declaration (or end of file)
    start = text.index(old)
    block_start = start + len(old)
    next_match = re.search(r"\n\t(column|measure) ", text[block_start:])
    block_end = block_start + next_match.start() if next_match else len(text)
    block = text[block_start:block_end]

    new_header = f"\tcolumn {quote(field + ' (No Agg)')}"
    if "sourceColumn:" in block:
        # sourceColumn already present further down in the block, don't duplicate it
        new = new_header
    else:
        new = new_header + f"\n\t\tsourceColumn: {field}"

    text = text[:start] + new + text[block_start:]
    open(TABLE_FILE, "w", encoding="utf-8").write(text)



def add_current_previous_period_measures(field):
    # TODO: paste in your existing current/previous period DAX here.
    # Branches on GRANULARITY_ALL because the definition changes depending
    # on whether "All" is a selectable granularity.
    if GRANULARITY_ALL:
        append(TABLE_FILE, f"""\tmeasure {quote(field + ' (Current Period)')} = 
                    VAR Granularity = SELECTEDVALUE ('_DateGranularity'[_DateGranularity Order])
                    RETURN
                        SWITCH (
                            Granularity,
                            0, CALCULATE([{field}], '{TABLE_NAME}'[_Is CPM]),
                            1, CALCULATE([{field}], '{TABLE_NAME}'[_Is CQTD]),
                            2, CALCULATE([{field}], '{TABLE_NAME}'[_Is CYTD]),
                            3, CALCULATE([{field}], '{TABLE_NAME}'[_Is CAYTD])
                        )""")
        append(TABLE_FILE, f"""\tmeasure {quote(field + ' (Previous Period)')} = 
            VAR Granularity = SELECTEDVALUE ('_DateGranularity'[_DateGranularity Order])
            RETURN
                SWITCH (
                    Granularity,
                    0, CALCULATE([{field}], '{TABLE_NAME}'[_Is PYPM]),
                    1, CALCULATE([{field}], '{TABLE_NAME}'[_Is PYQTD]),
                    2, CALCULATE([{field}], '{TABLE_NAME}'[_Is PYYTD]),
                    3, CALCULATE([{field}], '{TABLE_NAME}'[_Is PYAYTD])
                )""")
    else:
        append(TABLE_FILE, f"""\tmeasure {quote(field + ' (Current Period)')} = 
                            VAR Granularity = SELECTEDVALUE ('_DateGranularity'[_DateGranularity Order])
                            RETURN
                                SWITCH (
                                    Granularity,
                                    0, [{field}]
                                    1, CALCULATE([{field}], '{TABLE_NAME}'[_Is CPM]),
                                    2, CALCULATE([{field}], '{TABLE_NAME}'[_Is CQTD]),
                                    3, CALCULATE([{field}], '{TABLE_NAME}'[_Is CYTD]),
                                    4, CALCULATE([{field}], '{TABLE_NAME}'[_Is CAYTD])
                                )""")
        append(TABLE_FILE, f"""\tmeasure {quote(field + ' (Previous Period)')} = 
                    VAR Granularity = SELECTEDVALUE ('_DateGranularity'[_DateGranularity Order])
                    RETURN
                        SWITCH (
                            Granularity,
                            0, BLANK(),
                            1, CALCULATE([{field}], '{TABLE_NAME}'[_Is PYPM]),
                            2, CALCULATE([{field}], '{TABLE_NAME}'[_Is PYQTD]),
                            3, CALCULATE([{field}], '{TABLE_NAME}'[_Is PYYTD]),
                            4, CALCULATE([{field}], '{TABLE_NAME}'[_Is PYAYTD])
                        )""")




def add_delta_measures(field: str):
    append(TABLE_FILE, f"""\tmeasure {quote(field + ' Δ')} = 
        [{field} (Current Period)] - [{field} (Previous Period)]\n""")

    append(TABLE_FILE, f"""\tmeasure {quote(field + ' Δ%')} =
        DIVIDE([{field} (Current Period)] - [{field} (Previous Period)], [{field} (Previous Period)])\n""")


def process_numeric_field(field: str):
    rename_to_no_agg(field)
    if field != "ID":
        append(TABLE_FILE, f"\tmeasure {quote(field)} = SUM({quote(TABLE_NAME)}[{field} (No Agg)])\n")
    else:
        append(TABLE_FILE, f"\tmeasure {quote(field)} = COUNT({quote(TABLE_NAME)}[{field} (No Agg)])\n")


# RUNNING--------------------------
# comment out parts if not needed--------------------------------------

def main():
    create_date_granularity_parameter()
    create_globals_table()
    add_date_relationship()
    add_date_in_range()

    add_Is_Current_columns()
    add_Is_Previous_columns()

    for field in find_numeric_columns():
        process_numeric_field(field)                   # rename field to No Agg, and create a new SUM/COUNT measure
        add_current_previous_period_measures(field)    # create (current period) and (previous period) measures
        add_delta_measures(field)                      # create Δ and Δ% measures

    print(f"Done. Review {TABLE_FILE} and {RELATIONSHIPS_FILE}, then open the .pbip in Desktop.")


if __name__ == "__main__":
    main()