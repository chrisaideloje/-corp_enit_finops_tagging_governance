import os
from typing import List, Tuple, Optional
import pandas as pd


def load_account_ids(
    file_name_or_path: str,
    *,
    column: str = "AccountID",
    sheet_name: Optional[str] = None,
    search_subfolders: bool = True
) -> Tuple[List[str], pd.DataFrame]:
    """
    Load AWS account IDs from an Excel file.


    Args:
        file_name_or_path: Excel file name or absolute/relative path.
        column: Column in the sheet containing account IDs.
        sheet_name: Optional sheet name or index; if None, uses the first sheet.
        search_subfolders: If True and a bare file name is given, search cwd recursively.


    Returns:
        (account_ids, df): A list of account IDs and the loaded DataFrame.


    Raises:
        FileNotFoundError: If the file can't be located.
        ValueError: If the required column is missing or empty.
    """
    # Expand env vars and user (~)
    candidate = os.path.expandvars(os.path.expanduser(file_name_or_path))


    def _exists(p: str) -> bool:
        return os.path.isfile(p)


    # If it's a path and exists, use it
    if _exists(candidate):
        resolved = candidate
    else:
        # If only a filename was provided, try CWD and (optionally) walk subfolders
        base = os.path.basename(candidate)
        cwd_path = os.path.join(os.getcwd(), base)
        if _exists(cwd_path):
            resolved = cwd_path
        elif search_subfolders:
            resolved = None
            for dirpath, _, filenames in os.walk(os.getcwd()):
                if base in filenames:
                    resolved = os.path.join(dirpath, base)
                    break
            if not resolved:
                raise FileNotFoundError(
                    f"Excel file '{base}' not found in '{os.getcwd()}' or its subfolders."
                )
        else:
            raise FileNotFoundError(f"Excel file '{candidate}' not found.")


    # Read the Excel
    df = pd.read_excel(resolved, sheet_name=sheet_name)


    # If a specific sheet was selected, df is a DataFrame; if not and Excel has multiple sheets,
    # pandas may return a Dict[str, DataFrame]. Normalize to a DataFrame.
    if isinstance(df, dict):
        # Use the first sheet if none specified
        first_key = next(iter(df))
        df = df[first_key]


    # Validate column
    if column not in df.columns:
        raise ValueError(
            f"Required column '{column}' not found. Available columns: {list(df.columns)}"
        )


    # Drop NA and coerce to str, strip whitespace
    ids_series = (
        df[column]
        .dropna()
        .astype(str)
        .str.strip()
        .replace({"": pd.NA})
        .dropna()
    )


    if ids_series.empty:
        raise ValueError(f"No non-empty values found in column '{column}'.")


    account_ids = ids_series.tolist()
    return account_ids, df




# ---- Example usage (delete if importing elsewhere) ----
# if __name__ == "__main__":
#     # Works with absolute paths, relative paths, or just a filename in the repo
#     ids, df_raw = load_account_ids(
#         r"C:\Users\H630384\project\corp_enit_finops_tagging_governance\AWS\aws_accountid.xlsx",
#         column="AccountID",              # change if your column is different
#         sheet_name=None,                 # or "Sheet1"
#         search_subfolders=True
#     )
#     print(f"Loaded {len(ids)} account IDs")
#     # print(ids[:10])  # preview






def main():
    # Path to your Excel file (absolute or relative or just filename)
    excel_path = "C:\\Users\\H630384\\project\\corp_enit_finops_tagging_governance\\AWS\\aws_accountid.xlsx"
   
    # Call the function
    try:
        account_ids, df = load_account_ids(
            file_name_or_path=excel_path,
            column="account_ids",   # adjust if your column is named differently
            sheet_name=None,      # or "Sheet1"
            search_subfolders=True
        )


        # Use the IDs
        print(f"Loaded {len(account_ids)} AWS account IDs")
        print(account_ids[:10])  # preview first 10 IDs


        # You still have full DataFrame if you want to use other columns
        # print(df.head())


    except (FileNotFoundError, ValueError) as e:
        print(f" Error: {e}")




if __name__ == "__main__":
    main()



