# Car Maker Identifier - NHTSA Vehicle Parts Origin Tracker

> **Proof of Concept** | First Iteration

A Streamlit web application that visualizes where vehicle parts come from based on the **American Automobile Labeling Act (AALA)** reports from the National Highway Traffic Safety Administration (NHTSA).

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Background Story

Back in 2017, I stumbled upon the NHTSA's AALA data and was fascinated by the complexity of global automotive supply chains. Every vehicle sold in the US must disclose where its major components come from - engines, transmissions, and where final assembly takes place.

I wanted to build something to explore this data, but the challenge was significant: **the data lives in PDF files with inconsistent formatting, single-letter country codes, and messy table structures**. Parsing it seemed daunting, and I never had the time to tackle it.

Fast forward to now - this is the **first iteration** of that long-held idea finally coming to life! It's a proof of concept that demonstrates the feasibility of extracting, normalizing, and visualizing this unique dataset.

## What This Project Does

- **Extracts data from NHTSA PDF reports** (2020-2026 model years)
- **Normalizes country codes** (e.g., "G" to Germany, "J" to Japan, "H" to Hungary)
- **Cleans manufacturer names** (handles OCR errors, duplicates, variations)
- **Visualizes the data** through an interactive Streamlit dashboard with:
  - Overview of manufacturers and vehicle counts
  - Assembly location analysis by country
  - Engine and transmission source breakdowns
  - US/Canada content percentage analysis
  - Searchable data table with export functionality

## Data Source

### American Automobile Labeling Act (AALA)

The data comes from the **NHTSA Part 583 American Automobile Labeling Act Reports**:

https://www.nhtsa.gov/part-583-american-automobile-labeling-act-reports

#### What is the AALA?

The American Automobile Labeling Act (1992) requires all new passenger vehicles sold in the United States to have a label showing:

1. **% US/Canadian Parts Content** - Percentage of the vehicle's parts that originate from the US or Canada
2. **Country of Origin for Engine** - Where the engine was manufactured
3. **Country of Origin for Transmission** - Where the transmission was manufactured  
4. **Final Assembly Point** - City and country where the vehicle was assembled
5. **Country of Origin** - For major components

#### Country Codes Used

The reports use abbreviated country codes based on the official NHTSA key:

| Code | Country | Code | Country | Code | Country |
|------|---------|------|---------|------|---------|
| US | United States | G | Germany | J | Japan |
| M | Mexico | K | South Korea | CH | China |
| CN | Canada | UK | Great Britain | I | Italy |
| H | Hungary | PL | Poland | SP | Spain |
| TH | Thailand | IN | India | AU | Australia |

See `data_loader.py` for the complete mapping.

## Technical Challenges Solved

This project tackles several interesting data engineering challenges:

1. **PDF Table Extraction** - Using `pdfplumber` to extract tables from inconsistently formatted government PDFs
2. **Country Code Normalization** - Mapping single-letter codes (G, J, H, K, M, I) to full country names
3. **Manufacturer Name Cleaning** - Handling OCR errors, multiline concatenation, and name variations
4. **Data Validation** - Filtering out legend entries, invalid rows, and corrupted data

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/mjpon/car-maker-identifier.git
cd car-maker-identifier

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
# Run the Streamlit app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Refreshing the Data

To re-download and parse the latest NHTSA PDFs:

```bash
python data_loader.py
```

## Project Structure

```
car-maker-identifier/
├── app.py              # Streamlit web application
├── data_loader.py      # PDF parser and data processor
├── requirements.txt    # Python dependencies
├── data/
│   ├── MY2020_AALA.pdf # NHTSA reports (2020-2026)
│   ├── MY2021_AALA.pdf
│   ├── ...
│   └── nhtsa_data.csv  # Processed data
└── README.md
```

## Future Ideas

This is just the beginning! Potential future enhancements:

- Add historical data (pre-2020)
- Track changes in manufacturing locations over time
- Add vehicle-specific search and comparison
- Visualize supply chain on a world map
- Add EV-specific analysis (battery origins)
- API endpoint for programmatic access

## License

MIT License - feel free to use, modify, and distribute.

## Acknowledgments

- [NHTSA](https://www.nhtsa.gov/) for making this data publicly available
- [Streamlit](https://streamlit.io/) for the amazing dashboard framework
- [pdfplumber](https://github.com/jsvine/pdfplumber) for PDF parsing capabilities

---

*Built with curiosity and a long-held dream to finally parse that messy PDF data!*
