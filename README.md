# powerbi-model-generator

## Problem

During my internship creating a new Power BI dashboard project would take a long time, every dashboard would require
the same date table, granularity parameter, relationships, globals, layout, theme, relationships,
and at least 10+ table specific DAX measures/columns.

## Solution

- Create and Use a reusable **PBIP template** with a date table, layouts for visuals and tooltips, and a
  custom theme (colours, fonts, visual settings) as the starting point for every new dashboard.
- Create a **Python generator script** that for a given fact table in the template automatically generates:
  - The `_Globals` table
  - The `_DateGranularity` parameter
  - The relationship between the fact table and `_DateTable`
  - The fixed measures/columns

> **Note:** for confidentiality reasons, the template and fact table in this repository
> are basic generic examples for demonstration purposes. It does not include the internal custom template with its
> theme, visuals, or images used at the internship.

## Instructions

1. **Open template:**
   Open `template/SampleTemplate.pbip` in Power BI.

2. **Import a fact table:**
   Import a fact table (eg: `template/data/sample_fact_table.xlsx`) which **must**
   have a date field of type date, if it doesn't already then convert the field which will be used as the date field to type Date
   in Power BI first. Save the file.

3. **Fill in config:**
   Open `config.json` and fill in the required values (table name, date field
   name, etc.).

4. **Run the generator:**
   From the repository root, run:
   ```
   python generator/generator_script.py
   ```

5. Open the `.pbip` file again in Power BI to view the generated result.

## Requirements
- Power BI Desktop
- Python
