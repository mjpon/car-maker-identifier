"""Vehicle parts origin: explore NHTSA American Automobile Labeling Act (AALA) data."""

from pathlib import Path

import pandas as pd
import streamlit as st

import charts
import theme

st.set_page_config(
    page_title="Vehicle parts origin",
    page_icon=":material/directions_car:",
    layout="wide",
    initial_sidebar_state="collapsed",
)
theme.apply()

DATA_PATH = Path(__file__).parent / "data" / "nhtsa_data.csv"
AALA_URL = "https://www.nhtsa.gov/part-583-american-automobile-labeling-act-reports"
CONTENT_BANDS = [0, 10, 25, 50, 75, 100]
CONTENT_LABELS = ["0–10%", "10–25%", "25–50%", "50–75%", "75–100%"]


@st.cache_data
def load_data() -> pd.DataFrame:
    # "Raw" holds the unparsed PDF row; it is only useful for debugging the loader.
    return pd.read_csv(DATA_PATH).drop(columns=["Raw"], errors="ignore")


def plot(fig, key: str) -> None:
    # Streamlit derives a chart's ID from its content, so two identical charts (for example,
    # engine and transmission sources that happen to match) collide unless each has its own key.
    st.plotly_chart(fig, width="stretch", config=charts.PLOTLY_CONFIG, key=key)


def ranked_counts(series: pd.Series, limit: int, unit: str = "vehicles"):
    """Bar ranking of how often each value appears, ignoring blanks."""
    counts = series.dropna()
    counts = counts[counts != ""].value_counts().head(limit)
    return charts.ranking(counts.index, counts.values, unit=unit)


# ---------------------------------------------------------------- data and filters

df = load_data()

theme.masthead(
    f"Source: NHTSA AALA reports, model years {df['Year'].min()}–{df['Year'].max()}"
)
theme.title(
    "Where vehicle parts come from",
    "Every new passenger vehicle sold in the US carries a label that says where its "
    "engine, transmission and final assembly come from. This tool reads those reports "
    "so you can compare manufacturers, countries and model years.",
)

years = sorted(df["Year"].unique())

with st.container(key="filters"):
    col_year, col_make, col_line = st.columns([1, 2, 1.4])
    selected_years = col_year.multiselect(
        "Model year", options=years, default=[max(years)], placeholder="All years"
    )
    in_years = df[df["Year"].isin(selected_years)] if selected_years else df
    selected_makers = col_make.multiselect(
        "Manufacturer",
        options=sorted(in_years["Manufacturer"].dropna().unique()),
        placeholder="All manufacturers",
    )
    car_line = col_line.text_input("Car line", placeholder="For example, Civic or F-150")

filtered_df = in_years
if selected_makers:
    filtered_df = filtered_df[filtered_df["Manufacturer"].isin(selected_makers)]
if car_line:
    filtered_df = filtered_df[
        filtered_df["Car Line"].str.contains(car_line, case=False, na=False, regex=False)
    ]

if filtered_df.empty:
    theme.notice(
        "No vehicles match these filters. Remove a manufacturer or clear the car line search."
    )
    st.stop()

theme.board(
    [
        (f"{len(filtered_df):,}", "Vehicle models in this selection", True),
        (f"{filtered_df['Manufacturer'].nunique()}", "Manufacturers", False),
        (f"{filtered_df['Year'].nunique()}", "Model years", False),
        (f"{filtered_df['% US/Canada'].mean():.0f}%", "Average US and Canada parts content", False),
    ]
)

# ---------------------------------------------------------------- tabs

tab_overview, tab_assembly, tab_components, tab_content, tab_data = st.tabs(
    ["Overview", "Assembly", "Engines and transmissions", "Parts content", "Data"]
)

with tab_overview:
    theme.heading("Overview", "Models in the current selection, by manufacturer and over time.")

    theme.heading("Models by manufacturer", "The 15 manufacturers with the most models in this selection.", 3)
    plot(ranked_counts(filtered_df["Manufacturer"], 15, "models"), "overview_makers")

    # The trend ignores the model-year filter so it always shows the full history.
    trend_df = df
    if selected_makers:
        trend_df = trend_df[trend_df["Manufacturer"].isin(selected_makers)]
    if car_line:
        trend_df = trend_df[trend_df["Car Line"].str.contains(car_line, case=False, na=False, regex=False)]
    per_year = trend_df.groupby("Year").size()
    theme.heading(
        "Models reported per model year",
        "Covers all model years, whatever year is selected above. Reflects the manufacturer and car line filters.",
        3,
    )
    plot(charts.trend(per_year.index, per_year.values, unit="models"), "overview_trend")

with tab_assembly:
    theme.heading("Assembly", "Where the final vehicle is put together.")

    assembly = filtered_df["Assembly Country"].dropna()
    known = len(assembly)
    if known < len(filtered_df):
        theme.notice(
            f"Assembly country is reported for {known:,} of {len(filtered_df):,} vehicles in this "
            "selection. The rest are left out of this chart."
        )
    theme.heading("Vehicles by assembly country", "Top 20 countries.", 3)
    plot(ranked_counts(assembly, 20), "assembly_countries")

with tab_components:
    theme.heading("Engines and transmissions", "The country each major component comes from.")

    col_engine, col_trans = st.columns(2)
    with col_engine:
        theme.heading("Engine source", "Top 10 countries.", 3)
        plot(ranked_counts(filtered_df["Engine Source"], 10), "engine_sources")
    with col_trans:
        theme.heading("Transmission source", "Top 10 countries.", 3)
        plot(ranked_counts(filtered_df["Transmission Source"], 10), "transmission_sources")

with tab_content:
    theme.heading(
        "Parts content",
        "The label lists the share of parts from the US and Canada, plus up to two other "
        "countries that supply the most.",
    )

    col_bands, col_makers = st.columns(2)
    with col_bands:
        theme.heading("US and Canada content", "How many vehicles fall in each band.", 3)
        bands = pd.cut(
            filtered_df["% US/Canada"], bins=CONTENT_BANDS, labels=CONTENT_LABELS, include_lowest=True
        ).value_counts().sort_index()
        plot(charts.columns(CONTENT_LABELS, bands.values, unit="vehicles"), "content_bands")

    with col_makers:
        theme.heading("Highest US and Canada content", "Average by manufacturer, top 15.", 3)
        avg_content = (
            filtered_df.groupby("Manufacturer")["% US/Canada"].mean().sort_values(ascending=False).head(15)
        )
        plot(charts.ranking(avg_content.index, avg_content.values, unit="average", suffix="%"), "content_makers")

    primary = filtered_df[filtered_df["Primary Country"].notna() & (filtered_df["Primary Country"] != "")]
    col_main, col_share = st.columns(2)
    with col_main:
        theme.heading("Largest foreign source", "Vehicles by the country supplying the most non-US parts, top 15.", 3)
        plot(ranked_counts(primary["Primary Country"], 15), "content_primary_count")
    with col_share:
        theme.heading("Share from that country", "Average percent of parts content, top 15.", 3)
        avg_primary = (
            primary.groupby("Primary Country")["Primary %"].mean().sort_values(ascending=False).head(15)
        )
        plot(charts.ranking(avg_primary.index, avg_primary.values, unit="average", suffix="%"), "content_primary_share")

    theme.heading("Content breakdown for one manufacturer", level=3)
    makers = sorted(filtered_df["Manufacturer"].unique())
    largest = filtered_df["Manufacturer"].value_counts().idxmax()
    maker = st.selectbox("Manufacturer", makers, index=makers.index(largest), key="breakdown_maker")

    rows = filtered_df[filtered_df["Manufacturer"] == maker]
    us_canada = rows["% US/Canada"].mean()
    main_pct = rows["Primary %"].mean()
    second_pct = rows["Secondary %"].mean()
    other = max(0.0, 100 - us_canada - main_pct - second_pct)
    main_country = rows["Primary Country"].mode()
    main_country = main_country.iloc[0] if len(main_country) else "not itemized"
    segments = charts.composition_segments(
        us_canada, main_pct, second_pct, other, main_country=main_country
    )
    theme.legend([(name, color) for name, _, color, _ in segments])
    plot(charts.composition(segments), "content_breakdown")

with tab_data:
    theme.heading("Data", f"{len(filtered_df):,} vehicles match the filters above.")

    columns = [
        "Year", "Manufacturer", "Car Line", "% US/Canada", "Primary Country", "Primary %",
        "Secondary Country", "Secondary %", "Engine Source", "Transmission Source", "Assembly Country",
    ]
    table = filtered_df[columns].copy()
    # A share of 0% next to an empty country means "not listed", so show it blank.
    for country, share in [("Primary Country", "Primary %"), ("Secondary Country", "Secondary %")]:
        table[share] = table[share].astype("Int64").mask(table[country].isna() | (table[country] == ""))
    st.dataframe(
        table.fillna({c: "" for c in table.select_dtypes(exclude="number").columns}),
        hide_index=True,
        width="stretch",
        height=560,
        column_config={
            "Year": st.column_config.NumberColumn("Year", format="%d", width=64),
            "Manufacturer": st.column_config.TextColumn("Manufacturer", width=130),
            "Car Line": st.column_config.TextColumn("Car line", width=160),
            "% US/Canada": st.column_config.ProgressColumn(
                "US/Canada", min_value=0, max_value=100, format="%d%%", width=110
            ),
            "Primary Country": st.column_config.TextColumn("Main source", width=110),
            "Primary %": st.column_config.NumberColumn("Share", format="%d%%", width=64),
            "Secondary Country": st.column_config.TextColumn("Second source", width=120),
            "Secondary %": st.column_config.NumberColumn("Share", format="%d%%", width=64),
            "Engine Source": st.column_config.TextColumn("Engine", width=100),
            "Transmission Source": st.column_config.TextColumn("Transmission", width=120),
            "Assembly Country": st.column_config.TextColumn("Assembled in", width=110),
        },
    )
    st.download_button(
        "Download filtered data (CSV)",
        data=filtered_df.to_csv(index=False),
        file_name="nhtsa_filtered_data.csv",
        mime="text/csv",
    )

theme.footer(
    f'<p>Data: <a href="{AALA_URL}">NHTSA Part 583 American Automobile Labeling Act reports</a>.</p>'
    "<p>Country codes in the PDFs are normalized to full names (for example, MEX and MX become Mexico). "
    "Some ambiguous codes, such as CH, are interpreted from context. Blank values mean the report left "
    "the field empty or the parser could not read it.</p>"
)
