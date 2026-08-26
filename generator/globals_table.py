from core import *

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
        append(globals_file, f"""\tmeasure {quote('_Title - Latest Reporting Period (str)')} =
            SWITCH(
                [_Selected Granularity],
                0, "all",
                1, "month",
                2, "QTD",
                3, "YTD",
                4, "academic YTD"
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
        append(globals_file, f"""\tmeasure {quote('_Title - Latest Reporting Period (str)')} =
            SWITCH(
                [_Selected Granularity],
                0, "month",
                1, "QTD",
                2, "YTD",
                3, "academic YTD"
            )\n""")