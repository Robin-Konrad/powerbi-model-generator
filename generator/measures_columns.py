from core import *
import re


NUMERIC_TYPES = ("int64", "double", "decimal") # the data types that find_numeric_fields() will classify as numeric

def add_fixed_measures_columns():
    """
    Runs the pipeline for creation of the fixed columns and measures for every fact able.

    Creates _ReportingMonth, Date in Range, is_current/previous period flags, and for each numeric field renames it
    "field (No Agg)" and creates a SUM/COUNT measure, current/previous period measures, and delta measures.

    :param:             None
    :return:            None
    """
    add_reporting_month()
    add_date_in_range()

    add_is_current_columns()
    add_is_previous_columns()

    for field in find_numeric_fields():
        process_numeric_field(field)                   # rename field to No Agg, and create a new SUM/COUNT measure
        add_current_previous_period_measures(field)    # create (current period) and (previous period) measures
        add_delta_measures(field)                      # create Δ and Δ% measures

def add_reporting_month():
    """
    Creates a "_ReportingMonth" column which represents to the last day of the previous month.

    This is used as the latest reporting period, and is used in current and previous period calculations.

    :param:             None
    :return:            None
    """
    append(TABLE_FILE, f"\tcolumn {quote('_ReportingMonth')} = EOMONTH(TODAY(), -1)\n")


def add_date_in_range():
    """
    Creates a "Date In Range" column which represents all dates in the previous 24 months.

    The column is used to filter dates to the relevant date range.

    :param:             None
    :return:            None
    """
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
    """
    Creates "is current period" flag columns for month, quarter, year, and academic year periods.

    These return for each row a boolean representing if that rows date is within the current period.

    eg: _Is CPM (current period month) returns True if the rows date is withing the current month reporting period,
    and returns False otherwise.

    :param:             None
    :return:            None
    """
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
    """
        Creates "is previous year period" flag columns for month, quarter, year, and academic year periods.

        These return for each row a boolean representing if that rows date is within the previous year's instance
        of the current period.

        eg: _Is PYPM (previous year period month) returns True if the row's date is within the previous year's
        month that matches the current period's month, and returns False otherwise.

        :param:             None
        :return:            None
    """
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


def find_numeric_fields():
    """
    Searches the fact table tmdl file for lines beginning with "column X" and returns the names of all the columns
    which have a data type that matches one of the NUMERIC_TYPES.

    :param:             None
    :return:            list            string names of columns with a numeric data type
    """
    text = open(TABLE_FILE).read()
    pattern = r"\tcolumn (?:'([^']+)'|(\S+))\n\t\tdataType: (?:" + "|".join(NUMERIC_TYPES) + ")"
    return [quoted or plain for quoted, plain, *_ in re.findall(pattern, text)]


def rename_to_no_agg(field):
    """
    Renames a field from "field" to "field (No Agg)" in the fact table .tmdl file.

    :param field:       str, required        name of the field to rename
    :return:            None
    """
    text = open(TABLE_FILE, encoding="utf-8").read()

    # find the exact header line for the field, which could be "Column field"  or "Column 'field'"
    quoted_old = f"\tcolumn {quote(field)}"
    plain_old = f"\tcolumn {field}"

    if quoted_old in text:
        old = quoted_old
    elif plain_old in text:
        old = plain_old
    else:
        raise ValueError(f"Field '{field}' not found in {TABLE_FILE}")

    start = text.index(old)             # the index of the field's header line in the fact table .tmdl
    block_start = start + len(old)      # the index of the beginning of the field's block (after header line)

    new_header = f"\tcolumn {quote(field + ' (No Agg)')}"

    text = text[:start] + new_header + text[block_start:]
    open(TABLE_FILE, "w", encoding="utf-8").write(text)



def add_current_previous_period_measures(field):
    """
        Creates "field (Current Period)" and "field (Previous Period)" measures for a field.

        Branches on GRANULARITY_ALL boolean:
            if True selected granularity 0 represents "All" and should return all rows for current period and
            blank for the previous period as there is no previous ALL period possible.

            if False selected granularity 0 represents "Month" which returns all current month period (IS_CPM)
            rows for current period and returns all previous year month (Is_PYPM) rows for previous period.

        :param field:       str, required        name of the field to create period measures for
        :return:            None
    """
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


def add_delta_measures(field):
    """
        Creates "field Δ" and "field Δ%" measures for a field.

        "field Δ" represents the difference from the previous period to the current period.
        "field Δ%" represents the percentage difference.from the previous period to the current period.

        :param field:       str, required        name of the field measure the delta measures are based off
        :return:            None
    """

    append(TABLE_FILE, f"""\tmeasure {quote(field + ' Δ')} = 
        [{field} (Current Period)] - [{field} (Previous Period)]\n""")

    append(TABLE_FILE, f"""\tmeasure {quote(field + ' Δ%')} =
        DIVIDE([{field} (Current Period)] - [{field} (Previous Period)], [{field} (Previous Period)])\n""")


def process_numeric_field(field):
    """
        Processes a numeric field by renames it to "field (No Agg)" and creating an aggregation measure for the field.

        Required field to be of a numeric type data field.
        Uses COUNT aggregation for an id field and SUM for all others.

        :param field:       str, required        name of the numeric column to process
        :return:            None
    """
    rename_to_no_agg(field)
    if field.upper() != "ID":
        append(TABLE_FILE, f"\tmeasure {quote(field)} = SUM({quote(TABLE_NAME)}[{field} (No Agg)])\n")
    else:
        append(TABLE_FILE, f"\tmeasure {quote(field)} = COUNT({quote(TABLE_NAME)}[{field} (No Agg)])\n")