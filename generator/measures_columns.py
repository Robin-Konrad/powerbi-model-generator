from core import *
import re

# fixed columns and measures
def add_fixed_measures_columns():
    add_reporting_month()
    add_date_in_range()

    add_is_current_columns()
    add_is_previous_columns()

    for field in find_numeric_columns():
        process_numeric_field(field)                   # rename field to No Agg, and create a new SUM/COUNT measure
        add_current_previous_period_measures(field)    # create (current period) and (previous period) measures
        add_delta_measures(field)                      # create Δ and Δ% measures

def add_reporting_month():
    append(TABLE_FILE, f"\tcolumn {quote('_ReportingMonth')} = EOMONTH(TODAY(), -1)\n")

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

def add_is_current_columns():
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



def add_is_previous_columns():
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
    if field.upper() != "ID":
        append(TABLE_FILE, f"\tmeasure {quote(field)} = SUM({quote(TABLE_NAME)}[{field} (No Agg)])\n")
    else:
        append(TABLE_FILE, f"\tmeasure {quote(field)} = COUNT({quote(TABLE_NAME)}[{field} (No Agg)])\n")