from core import *

# creating _DateGranularity parameter
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

