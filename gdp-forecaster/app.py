# Paolo Velasco, ptvelasc@usc.edu
# Description: This project allows users to explore and visualize GDP data
# for different countries. Users can view historical data, see GDP growth rates,
# and forecast future projections via machine learning through a web app.

# IMPORTANT NOTE: Please run db_actions.py first to populate the database before running this app!


from flask import Flask, redirect, render_template, request, session, url_for, send_file
import os
import io
import sqlite3 as sl
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Initializes Flask
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = "gdp_analysis.db"  # database name


@app.route("/")
def home():
    # Clears projection-related session variables
    session.pop('projection_year', None)
    session.pop('predicted_gdp', None)
    session.pop('year', None)

    print("DEBUG: Home page loaded. Session variables cleared.")

    # Renders the homepage with the locales and data visualization options
    return render_template(
        "home.html",
        locales=db_get_locales(),
        message="Paolo's GDP Visualizer:",
        options={"raw": "Graph of GDP", "rate": "GDP Growth Rates"}
    )


@app.route("/submit_locale", methods=["POST"])
def submit_locale():
    # Check if locale or data_request is missing
    if not request.form.get("locale") or not request.form.get("data_request"):
        print("DEBUG: Missing locale or data_request in form.")
        return redirect(url_for("home"))

    # Clears projection-related session variables when selecting new locale
    session.pop('projection_year', None)
    session.pop('predicted_gdp', None)
    session.pop('year', None)

    # Sets the locale and data request type
    session["locale"] = request.form["locale"]
    session["data_request"] = request.form["data_request"]

    print(f"DEBUG: Locale selected: {session['locale']}, Data request: {session['data_request']}")

    # Redirects to the appropriate view
    return redirect(url_for("locale_current", data_request=session["data_request"], locale=session["locale"]))


@app.route("/api/gdp/<data_request>/<locale>")
def locale_current(data_request, locale):
    # Clears projection-related session variables
    session.pop('projection_year', None)
    session.pop('predicted_gdp', None)
    session.pop('year', None)

    print(f"DEBUG: Loaded data for {locale} with request {data_request}")

    # Renders the view for the selected country and data request type
    return render_template(
        "locale.html",
        locale=locale,
        data_request=data_request,
        project=False
    )


@app.route("/submit_projection", methods=["POST"])
def submit_projection():
    # Redirects to home if no locale is selected
    if 'locale' not in session:
        print("DEBUG: Locale missing from session during projection submission.")
        return redirect(url_for("home"))

    # Stores the projection year in the session
    session["year"] = request.form.get("year")

    # Redirects to home if no year is provided
    if not session["year"]:
        print("DEBUG: Year not provided for projection.")
        return redirect(url_for("home"))

    print(f"DEBUG: Projection year set to {session['year']}")

    # Redirects to the projection view
    return redirect(
        url_for(
            "locale_projection",
            data_request=session["data_request"],
            locale=session["locale"]
        )
    )


@app.route("/api/gdp/<data_request>/projection/<locale>")
def locale_projection(data_request, locale):
    # Redirects to home if no projection year is set
    year = session.get("year")
    if not year:
        print("DEBUG: Projection year is missing in session.")
        return redirect(url_for("home"))

    print(f"DEBUG: Rendering projection for {locale} with year {year}")

    # Renders the view with the projected data
    return render_template(
        "locale.html",
        locale=locale,
        data_request=data_request,
        project=True,
        year=year
    )


@app.route("/fig/<data_request>/<locale>")
def fig(data_request, locale):
    # Generates the figure for the requested data visualization
    print(f"DEBUG: Generating figure for {data_request} in {locale}. Projection year: {session.get('year')}")
    fig = create_figure(data_request, locale)

    # Converts the figure to an image
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype="image/png")


def create_figure(data_request, locale):
    df = db_create_dataframe(data_request, locale)

    if df.empty or "Year" not in df.columns or "GDP" not in df.columns:
        fig = Figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.text(0.5, 0.5, "No Data Available", fontsize=15, ha='center')
        ax.set_axis_off()
        return fig

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year", "GDP"]).sort_values(by="Year").reset_index(drop=True)

    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)

    first_year = int(df["Year"].iloc[0])
    last_year = int(df["Year"].iloc[-1])
    tick_years = list(range(first_year, last_year + 1, 5))

    if session.get("year"):
        projection_year = int(session["year"])
        while tick_years[-1] < projection_year:
            tick_years.append(tick_years[-1] + 5)

    # ---------------- RAW (GDP PER CAPITA) ----------------
    if data_request == "raw":
        fig.suptitle(f"GDP per Capita for {locale}")

        ax.plot(df["Year"], df["GDP"], marker="o", label="GDP per Capita")
        ax.set_xticks(tick_years)
        ax.grid(True, linestyle="--", alpha=0.5)

        if session.get("year"):
            y = df["GDP"].values
            X = df["Year"].values.reshape(-1, 1)
            projection_year = int(session["year"])

            regr = LinearRegression()
            regr.fit(X, y)
            predicted_value = regr.predict([[projection_year]])[0]

            new_row = pd.DataFrame([{'Year': projection_year, 'GDP': predicted_value}])
            df = pd.concat([df, new_row], ignore_index=True).sort_values(by="Year")

            regression_years = np.arange(first_year, projection_year + 1)
            regression_values = regr.predict(regression_years.reshape(-1, 1))

            ax.plot(regression_years, regression_values, linestyle="--", color="red", label="Projection Line")
            ax.scatter(projection_year, predicted_value, color="red", s=100,
                       label=f"Projection ({projection_year})")

            ax.annotate(
                f"${predicted_value:,.0f}",
                (projection_year, predicted_value),
                textcoords="offset points",
                xytext=(10, 0),
                fontsize=12,
                color="red",
                fontweight='bold'
            )

        ax.set_xlabel("Year")
        ax.set_ylabel("GDP per Capita (USD)")
        ax.legend()

    # ---------------- GROWTH RATE ----------------
    elif data_request == "rate":
        df["GDP Growth Rate"] = df["GDP"].pct_change() * 100
        df = df.dropna(subset=["GDP Growth Rate"])

        fig.suptitle(f"GDP per Capita Growth Rate for {locale}")

        ax.plot(df["Year"], df["GDP Growth Rate"], marker="o", label="Growth Rate")
        ax.set_xticks(tick_years)
        ax.grid(True, linestyle="--", alpha=0.5)

        if session.get("year"):
            y = df["GDP Growth Rate"].values
            X = df["Year"].values.reshape(-1, 1)
            projection_year = int(session["year"])

            regr = LinearRegression()
            regr.fit(X, y)
            predicted_value = regr.predict([[projection_year]])[0]

            new_row = pd.DataFrame([{'Year': projection_year, 'GDP Growth Rate': predicted_value}])
            df = pd.concat([df, new_row], ignore_index=True).sort_values(by="Year")

            regression_years = np.arange(first_year, projection_year + 1)
            regression_values = regr.predict(regression_years.reshape(-1, 1))

            ax.plot(regression_years, regression_values, linestyle="--", color="green", label="Projection Line")
            ax.scatter(projection_year, predicted_value, color="green", s=100,
                       label=f"Projection ({projection_year})")

            ax.annotate(
                f"{predicted_value:.2f}%",
                (projection_year, predicted_value),
                textcoords="offset points",
                xytext=(10, 0),
                fontsize=12,
                color="green",
                fontweight='bold'
            )

            ax.set_xlim(first_year, projection_year + 2)

        ax.set_xlabel("Year")
        ax.set_ylabel("GDP per Capita Growth Rate (%)")
        ax.legend()

    return fig



def db_create_dataframe(data_request, locale):
    # Queries the database for GDP data for the selected locale
    conn = sl.connect(db)
    try:
        query = "SELECT Year, GDP FROM gdp_data WHERE Country = ? ORDER BY Year"
        print(f"DEBUG: Running SQL query for {locale}")
        df = pd.read_sql_query(query, conn, params=[locale])
        print(f"DEBUG: Query result: {df.shape[0]} rows fetched.")
        return df
    finally:
        conn.close()


def db_get_locales():
    # Queries the database for all distinct countries
    conn = sl.connect(db)
    try:
        query = "SELECT DISTINCT Country FROM gdp_data ORDER BY Country"
        result = pd.read_sql_query(query, conn)
        return result['Country'].tolist()
    finally:
        conn.close()


@app.route('/<path:path>')
def catch_all(path):
    # Redirects invalid endpoint requests to the homepage
    print(f"DEBUG: Invalid path requested: {path}")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)
