import pandas as pd
from datetime import datetime
import glob
import os

# add vertically

# files = glob.glob(os.path.join("output_2026-08-*.csv"))
#
# dataframes = []
#
# for file in files:
#     try:
#         df = pd.read_csv(file)  # keep header!
#         df['source_file'] = os.path.basename(file)
#         dataframes.append(df)
#
#     except Exception as e:
#         print(f"Error reading {file}: {e}")
#
# if not dataframes:
#     print("No valid files found.")
#
#
# merged_df = pd.concat(dataframes, ignore_index=True)
#
# timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# merged_df.to_csv(os.path.join(f"merged_output_best_{timestamp}.csv"), index=False)
#
# print("Merged file saved.")


# add horizontally








# Find all input CSV files
files = sorted(glob.glob("output_2026-08-*.csv"))

merged_df = None


for file in files:

    try:
        df = pd.read_csv(file)

        # Check required columns
        required_columns = {"Address", "Availability", "Timestamp"}

        if not required_columns.issubset(df.columns):
            print(f"Skipping {file}: required columns missing.")
            continue

        # Get timestamp
        timestamp = str(df["Timestamp"].iloc[0])

        # Keep only the columns we need
        temp = df[["Address", "Availability"]].copy()

        # Number each occurrence of an address
        temp["occurrence"] = temp.groupby("Address").cumcount()

        # Create unique key
        temp["key"] = (
            temp["Address"].astype(str)
            + "___"
            + temp["occurrence"].astype(str)
        )

        # Set key as index
        temp.set_index("key", inplace=True)

        # --------------------------------------------------
        # FIRST FILE
        # --------------------------------------------------

        if merged_df is None:

            merged_df = temp[["Address", "Availability"]].copy()

            merged_df.rename(
                columns={"Availability": timestamp},
                inplace=True
            )

        # --------------------------------------------------
        # FOLLOWING FILES
        # --------------------------------------------------

        else:

            # Add any completely new addresses/occurrences
            new_keys = temp.index.difference(merged_df.index)

            if len(new_keys) > 0:

                new_rows = temp.loc[
                    new_keys,
                    ["Address"]
                ].copy()

                merged_df = pd.concat(
                    [merged_df, new_rows],
                    axis=0
                )

            # Make sure the timestamp column exists
            if timestamp not in merged_df.columns:

                merged_df[timestamp] = pd.NA

            # Get values from this file
            values = temp["Availability"]

            # Match using the key
            common_keys = values.index.intersection(
                merged_df.index
            )

            # --------------------------------------------------
            # If timestamp already exists:
            # update the corresponding rows
            # --------------------------------------------------

            merged_df.loc[
                common_keys,
                timestamp
            ] = values.loc[common_keys]

        # print(f"Processed: {os.path.basename(file)}")


    except Exception as e:
        print(f"Error reading {file}: {e}")


# --------------------------------------------------
# No files check
# --------------------------------------------------

if merged_df is None:

    print("No valid files found.")
    exit()


# --------------------------------------------------
# Reconstruct Address column
# --------------------------------------------------

# Address is already stored, but make sure it is correct
# for rows introduced by later files.

address_from_key = (
    merged_df.index
    .astype(str)
    .str.rsplit("___", n=1)
    .str[0]
)

merged_df["Address"] = (
    merged_df["Address"]
    .fillna(pd.Series(
        address_from_key,
        index=merged_df.index
    ))
)


# --------------------------------------------------
# Put Address FIRST
# --------------------------------------------------

timestamp_columns = [
    col for col in merged_df.columns
    if col != "Address"
]

merged_df = merged_df[
    ["Address"] + timestamp_columns
]


# --------------------------------------------------
# Reset index
# --------------------------------------------------

merged_df.reset_index(drop=True, inplace=True)


# --------------------------------------------------
# Save
# --------------------------------------------------

save_timestamp = datetime.now().strftime(
    "%Y-%m-%d_%H-%M-%S"
)

output_file = (
    f"merged_output_{save_timestamp}.csv"
)

merged_df.to_csv(
    output_file,
    index=False
)


# print()
# print("Merged file saved:")
# print(output_file)
#
# print(f"Rows: {len(merged_df)}")
# print(f"Columns: {len(merged_df.columns)}")