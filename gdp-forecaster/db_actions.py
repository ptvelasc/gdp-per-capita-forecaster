# Paolo Velasco, ptvelasc@usc.edu
# Description: This script manages the creation of a SQLite database for GDP data,
# transforms and stores the data from a CSV file into the database, and allows querying
# of GDP data for specific countries and time periods.

# IMPORTANT NOTE: Please run this file first before app.py to populate the database before running the app!


import sqlite3 as sl
import pandas as pd

# Names the database file
db = "gdp_analysis.db"


def create_table():
    # Creates the SQLite database and a table for storing GDP data with constraints
    conn = sl.connect(db)
    curs = conn.cursor()

    # Creates table with constraints for data integrity
    curs.execute('''
        CREATE TABLE IF NOT EXISTS gdp_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,  
            year INTEGER NOT NULL CHECK(year > 0),
            gdp REAL NOT NULL CHECK(gdp >= 0)     
        )
    ''')
    conn.commit()
    conn.close()
    print("Table created")


def store_data():
    """
    Reads the CSV file containing GDP data, turns the data into a suitable format,
    filters unnecessary rows, and then stores it into the SQLite database.
    """
    # Loads the dataset
    csv_path = "gdp.csv"  # Path to the CSV file
    df = pd.read_csv(csv_path)

    # Removes columns for years 2024–2028 since they exist as IMF projections
    columns_to_remove = [str(year) for year in range(2024, 2029)]
    df = df.drop(columns=[col for col in columns_to_remove if col in df.columns])

    # Transforms data from wide format (columns as years) to long format (rows as years)
    df_long = df.melt(id_vars=["Country"], var_name="Year", value_name="GDP")

    # Cleans the data
    df_long = df_long.dropna(subset=["Year", "GDP"])  # Remove rows with missing values
    df_long = df_long[df_long["GDP"] > 0]  # Remove non-positive GDP values
    df_long = df_long.drop_duplicates(subset=["Country", "Year"])  # Remove duplicates

    # Stores the data into the database
    conn = sl.connect(db)
    df_long.to_sql("gdp_data", conn, if_exists="replace", index=False)
    conn.close()
    print("Data stored")


def query_data(country, year_start, year_end):
    """
    Queries the database for GDP data for a specific country and time range
    :param country: Name of the country
    :param year_start: Start year of the range
    :param year_end: End year of the range
    :return: A list of rows containing the year and GDP for the specified range
    """
    conn = sl.connect(db)
    cursor = conn.cursor()

    # Execute SQL query
    cursor.execute('''
        SELECT year, gdp FROM gdp_data
        WHERE country = ? AND year BETWEEN ? AND ?
        ORDER BY year
    ''', (country, year_start, year_end))

    rows = cursor.fetchall()
    conn.close()

    return rows


def main():
    # Creates the table
    create_table()
    # Stores data into the database
    store_data()


if __name__ == "__main__":
    main()
