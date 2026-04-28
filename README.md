# GDP per Capita Visualizer
 
A Flask-based web app that visualizes GDP per capita data by locale, with optional linear regression projections.
 
## Features
 
- **GDP per Capita** – line chart of raw GDP values over time
- **Growth Rate** – year-over-year percentage change chart
- **Projections** – optional linear regression forecast to a user-specified year
## Requirements
 
```
flask
pandas
numpy
scikit-learn
matplotlib
```
 
## Usage
 
1. Install dependencies:
   ```bash
   pip install flask pandas numpy scikit-learn matplotlib
   ```
 
2. Run the app:
   ```bash
   flask run
   ```
 
3. Select a locale and chart type (`raw` or `rate`). Optionally enter a projection year to see a forecast line and annotated predicted value.
## How It Works
 
| Mode | Description |
|------|-------------|
| `raw` | Plots GDP per capita (USD) over time |
| `rate` | Plots year-over-year GDP growth rate (%) |
 
When a projection year is set in the session, a `LinearRegression` model is fit on historical data and extrapolated to that year. The predicted value is annotated on the chart.
 
## Notes
 
- Data is fetched via `db_create_dataframe(data_request, locale)`
- Projection year is stored in Flask's `session["year"]`
- Falls back to a "No Data Available" placeholder if the dataframe is empty or missing required columns
