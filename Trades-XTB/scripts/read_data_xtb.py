import pandas as pd
import os
import re
from glob import glob

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data")


def extract_account(filename: str) -> str:
    """
    Extrae el número de cuenta desde el nombre del archivo.
    Ej: USD_52793784_2006-01-01_2026-06-03.xlsx -> 52793784
    """
    match = re.search(r"USD_(\d+)_", filename)
    return match.group(1) if match else None


def clean_numeric(value):
    """
    Convierte valores tipo '317,58' -> 317.58
    """
    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.strip()

        if value == "":
            return None

        return float(value.replace(",", "."))

    return value


def upsert_csv(new_df, csv_path, key_columns):
    """
    Inserta registros nuevos y actualiza existentes.
    Conserva la última versión encontrada.
    """

    if os.path.exists(csv_path):

        old_df = pd.read_csv(
            csv_path,
            dtype=str,
            keep_default_na=False
        )

        new_df = new_df.astype(str)

        merged = pd.concat(
            [old_df, new_df],
            ignore_index=True
        )

        merged = merged.drop_duplicates(
            subset=key_columns,
            keep="last"
        )

        return merged

    return new_df


def process_closed_positions(file_path, account_id):

    df = pd.read_excel(
        file_path,
        sheet_name="Closed Positions",
        skiprows=4
    )

    # Eliminar filas resumen de XTB
    df = df[
        (df["Position ID"].notna()) &
        (df["Open Time (UTC)"].notna()) &
        (df["Close Time (UTC)"].notna())
    ]

    # Protección adicional
    if "Instrument" in df.columns:
        df = df[
            ~df["Instrument"]
                .astype(str)
                .str.contains(
                    "Profit/loss",
                    case=False,
                    na=False
                )
        ]

    df = df.rename(columns={
        "Instrument": "Instrument",
        "Category": "Category",
        "Ticker": "Ticker",
        "Type": "Type",
        "Volume": "Volume",
        "Open Price": "Open Price",
        "Open Time (UTC)": "Open Time (UTC)",
        "Close Price": "Close Price",
        "Close Time (UTC)": "Close Time (UTC)",
        "Profit/Loss": "Profit/Loss",
        "Purchase Value": "Purchase Value",
        "Sale Value": "Sale Value",
        "Commission": "Commission",
        "Margin": "Margin",
        "Swap": "Swap",
        "Position ID": "ID"
    })

    numeric_cols = [
        "Volume",
        "Open Price",
        "Close Price",
        "Profit/Loss",
        "Purchase Value",
        "Sale Value",
        "Commission",
        "Margin",
        "Swap"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric)

    df["Open Date"] = pd.to_datetime(
        df["Open Time (UTC)"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df["Close Date"] = pd.to_datetime(
        df["Close Time (UTC)"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df.drop(
        columns=[
            "Open Time (UTC)",
            "Close Time (UTC)"
        ],
        inplace=True,
        errors="ignore"
    )

    df["id_account"] = account_id
    df["Time"] = ""
    df["Amount"] = ""

    return df


def process_cash_operations(file_path, account_id):

    df = pd.read_excel(
        file_path,
        sheet_name="Cash Operations",
        skiprows=4
    )

    df = df.rename(columns={
        "Type": "Type",
        "Time": "Time",
        "Amount": "Amount",
        "ID": "ID"
    })

    df["Time"] = pd.to_datetime(
        df["Time"],
        errors="coerce"
    )

    df["Amount"] = df["Amount"].apply(clean_numeric)

    df["id_account"] = account_id

    df["Type"] = (
        df["Type"]
        .astype(str)
        .str.strip()
    )

    allowed_types = [
        "Deposit",
        "Dividend",
        "Dividend equivalent",
        "Withdrawal"
    ]

    df = df[
        df["Type"].isin(allowed_types)
    ]

    df = df[
        [
            "Type",
            "Time",
            "Amount",
            "id_account"
        ]
    ]

    df["Time"] = df["Time"].dt.strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )

    return df


def main():

    excel_files = glob(
        os.path.join(DATA_PATH, "*.xlsx")
    )

    all_trades = []
    all_transactions = []

    for file in excel_files:

        filename = os.path.basename(file)
        account_id = extract_account(filename)

        if not account_id:
            continue

        print(
            f"Procesando cuenta {account_id} -> {filename}"
        )

        try:

            trades = process_closed_positions(
                file,
                account_id
            )

            cash = process_cash_operations(
                file,
                account_id
            )

            all_trades.append(trades)
            all_transactions.append(cash)

        except Exception as e:
            print(
                f"Error en {filename}: {e}"
            )

    if not all_trades:
        print("No se encontraron operaciones.")
        return

    trades_df = pd.concat(
        all_trades,
        ignore_index=True
    )

    cash_df = pd.concat(
        all_transactions,
        ignore_index=True
    )

    trades_columns = [
        "Instrument",
        "Category",
        "Ticker",
        "Type",
        "Volume",
        "Open Price",
        "Open Date",
        "Close Price",
        "Close Date",
        "Profit/Loss",
        "Purchase Value",
        "Sale Value",
        "Stop Loss",
        "Take Profit",
        "Commission",
        "Margin",
        "Swap",
        "id_account",
        "Time",
        "Amount",
        "ID"
    ]

    trades_df = trades_df.reindex(
        columns=trades_columns
    )

    output_trades = os.path.join(
        DATA_PATH,
        "trades_xtb.csv"
    )

    output_cash = os.path.join(
        DATA_PATH,
        "transactions_xtb.csv"
    )

    # UPSERT TRADES
    trades_df = upsert_csv(
        trades_df,
        output_trades,
        ["ID", "id_account"]
    )

    # UPSERT CASH
    cash_df = upsert_csv(
        cash_df,
        output_cash,
        [
            "Type",
            "Time",
            "Amount",
            "id_account"
        ]
    )

    trades_df.to_csv(
        output_trades,
        index=False
    )

    cash_df.to_csv(
        output_cash,
        index=False
    )

    print(
        f"✔ Trades guardados: {len(trades_df)}"
    )

    print(
        f"✔ Cash guardados: {len(cash_df)}"
    )

    print("✔ Archivos generados:")
    print(output_trades)
    print(output_cash)


if __name__ == "__main__":
    main()