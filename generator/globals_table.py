import generator.core as core

def create_globals_table():
    """
        Creates an empty "_Globals" calculated table, and adds fixed set of global measures.

        :param:             None
        :return:            None
    """
    globals_file = f"{core.TABLES_DIR}/_Globals.tmdl"

    content = """table _Globals
    partition _Globals = calculated
    \tmode: import
    \tsource = { BLANK() }"""


    with open(globals_file, "w", encoding="utf-8") as f:
        f.write(content)

    create_globals_measures(globals_file)

def create_globals_measures(globals_file):
    """
        Creates fixed set of measures to the _Globals table.

        Fixed set of global measure includes '_Selected Granularity', '_Academic Year Month Start', 'Date (str)',
        '_Title - Reporting Period', '_Title - Reporting Period (Delta Explainer)',
        '_Title - Reporting Period (Text Box Fmt)', and '_Title - Latest Reporting Period (str)'.

        DAX logic for global measure branches based of the GRANULARITY_ALL boolean:
            If True it adds logic for granularity "All" selector.
            If False it doesn't add logic for granularity "All" selector.


        :param globals_file:   str, required        path of the _Globals .tmdl table file to add measures to.
        :return:               None
        """
    core.append(globals_file, f"\n\tmeasure {core.quote('_Selected Granularity')} = SELECTEDVALUE('_DateGranularity'[_DateGranularity Order], 0)\n")
    core.append(globals_file, f"\tmeasure {core.quote('_Academic Year Month Start')} = {core.ACADEMIC_MONTH}\n")

    if core.GRANULARITY_ALL:
        core.append(globals_file, f"""\tmeasure {core.quote('Date (str)')} =
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
        core.append(globals_file ,f"""\tmeasure {core.quote('_Title - Reporting Period')} =
            SWITCH(
                [_Selected Granularity],
                0, " ",
                1, "Prior Month",
                2, "QTD",
                3, "YTD",
                4, "AYTD"
            )\n""")
        core.append(globals_file, f"""\tmeasure {core.quote('_Title - Reporting Period (Delta Explainer)')} =
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
        core.append(globals_file ,f"""\tmeasure {core.quote('_Title - Reporting Period (Text Box Fmt)')} =
            SWITCH(
                [_Selected Granularity],
                0, " ",
                1, "Prior Month",
                2, "QTD",
                3, "YTD",
                4, "AYTD"
            )\n""")
        core.append(globals_file, f"""\tmeasure {core.quote('_Title - Latest Reporting Period (str)')} =
            SWITCH(
                [_Selected Granularity],
                0, "all",
                1, "month",
                2, "QTD",
                3, "YTD",
                4, "academic YTD"
            )\n""")
    else:
        core.append(globals_file, f"""\tmeasure {core.quote('Date (str)')} =
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
        core.append(globals_file, f"""\tmeasure {core.quote('_Title - Reporting Period')} =
            SWITCH(
                [_Selected Granularity],
                    0, "Prior Month",
                    1, "QTD",
                    2, "YTD",
                    3, "AYTD"
                )\n""")
        core.append(globals_file, f"""\tmeasure {core.quote('_Title - Reporting Period (Delta Explainer)')} =
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
        core. append(globals_file, f"""\tmeasure {core.quote('_Title - Reporting Period (Text Box Fmt)')} =
            SWITCH(
                [_Selected Granularity],
                0, "Prior Month",
                1, "QTD",
                2, "YTD",
                3, "AYTD"
            )\n""")
        core.append(globals_file, f"""\tmeasure {core.quote('_Title - Latest Reporting Period (str)')} =
            SWITCH(
                [_Selected Granularity],
                0, "month",
                1, "QTD",
                2, "YTD",
                3, "academic YTD"
            )\n""")