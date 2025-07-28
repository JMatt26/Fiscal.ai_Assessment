import pandas as pd

def prune_excel_to_numeric_rows(input_path: str, output_path: str) -> None:
    """
    Prunes all rows from all sheets in an Excel file where any value (except the first column) is non-numeric.
    Saves the cleaned result into a new Excel workbook with the same sheet structure.
    
    Args:
        input_path (str): Path to the original Excel file.
        output_path (str): Path to the cleaned Excel file to be written.
    """
    xls = pd.ExcelFile(input_path)
    sheet_names = xls.sheet_names

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet in sheet_names:
            df = xls.parse(sheet)
            if df.empty:
                continue

            line_items = df.iloc[:, 0]
            values = df.iloc[:, 1:]

            def is_numeric(x):
                try:
                    float(str(x).replace(",", "").replace(" ", ""))
                    return True
                except (ValueError, TypeError):
                    return False

            mask = values.applymap(is_numeric)
            valid_rows = mask.all(axis=1)

            cleaned_df = pd.concat([
                line_items[valid_rows].reset_index(drop=True),
                values[valid_rows].reset_index(drop=True)
            ], axis=1)
            cleaned_df.columns = df.columns

            cleaned_df.to_excel(writer, sheet_name=sheet[:31], index=False)
