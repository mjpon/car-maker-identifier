import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="NHTSA Auto Parts Origin",
    page_icon="🚗",
    layout="wide"
)

# Country flag emojis mapping (based on NHTSA AALA document key)
COUNTRY_FLAGS = {
    "United States": "🇺🇸",
    "Mexico": "🇲🇽",
    "Canada": "🇨🇦",
    "Japan": "🇯🇵",
    "Germany": "🇩🇪",
    "South Korea": "🇰🇷",
    "United Kingdom": "🇬🇧",
    "Italy": "🇮🇹",
    "France": "🇫🇷",
    "Sweden": "🇸🇪",
    "Hungary": "🇭🇺",
    "Austria": "🇦🇹",
    "Belgium": "🇧🇪",
    "China": "🇨🇳",
    "Czech Republic": "🇨🇿",
    "Finland": "🇫🇮",
    "Spain": "🇪🇸",
    "Slovakia": "🇸🇰",
    "Turkey": "🇹🇷",
    "Brazil": "🇧🇷",
    "South Africa": "🇿🇦",
    "Australia": "🇦🇺",
    "Poland": "🇵🇱",
    "Thailand": "🇹🇭",
    "Indonesia": "🇮🇩",
    "Malaysia": "🇲🇾",
    "Argentina": "🇦🇷",
    "Taiwan": "🇹🇼",
    "Vietnam": "🇻🇳",
    "India": "🇮🇳",
    "Portugal": "🇵🇹",
    "Netherlands": "🇳🇱",
    "Russia": "🇷🇺",
    "Serbia": "🇷🇸",
    "Denmark": "🇩🇰",
    "Philippines": "🇵🇭",
    "Romania": "🇷🇴",
    "Singapore": "🇸🇬",
    "Cuba": "🇨🇺",
    "Other": "🌍",
}

@st.cache_data
def load_data():
    """Load the NHTSA data"""
    return pd.read_csv("data/nhtsa_data.csv")

def get_flag(country):
    """Get flag emoji for country"""
    if pd.isna(country) or country == "":
        return ""
    return COUNTRY_FLAGS.get(country, "🌍")

# Load data
df = load_data()

# Title and description
st.title("🚗 NHTSA Vehicle Parts Origin Tracker")
st.markdown("""
Explore where vehicle parts come from based on the **American Automobile Labeling Act (AALA)** reports.
View assembly locations, engine sources, transmission origins, and more across different manufacturers and years.
""")

# Sidebar filters
st.sidebar.header("Filters")

# Year filter
years = sorted(df['Year'].unique())
selected_years = st.sidebar.multiselect(
    "Select Year(s)",
    options=years,
    default=[max(years)] if years else []
)

# Filter data by year
filtered_df = df[df['Year'].isin(selected_years)] if selected_years else df

# Manufacturer filter
manufacturers = sorted(filtered_df['Manufacturer'].dropna().unique())
selected_manufacturers = st.sidebar.multiselect(
    "Select Manufacturer(s)",
    options=manufacturers,
    default=[]
)

# Apply manufacturer filter
if selected_manufacturers:
    filtered_df = filtered_df[filtered_df['Manufacturer'].isin(selected_manufacturers)]

# Car Line search
car_line_search = st.sidebar.text_input("Search Car Line")
if car_line_search:
    filtered_df = filtered_df[
        filtered_df['Car Line'].str.contains(car_line_search, case=False, na=False)
    ]

# Display metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Vehicles", len(filtered_df))
with col2:
    st.metric("Manufacturers", filtered_df['Manufacturer'].nunique())
with col3:
    st.metric("Years Covered", filtered_df['Year'].nunique())

# Tab layout
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🏭 Assembly Locations",
    "⚙️ Component Origins",
    "📈 Content Percentages",
    "📋 Data Table"
])

with tab1:
    st.header("Overview")
    
    # Top manufacturers by count
    st.subheader("Top Manufacturers by Vehicle Count")
    mfg_counts = filtered_df['Manufacturer'].value_counts().head(15)
    fig_mfg = px.bar(
        x=mfg_counts.values,
        y=mfg_counts.index,
        orientation='h',
        labels={'x': 'Number of Vehicles', 'y': 'Manufacturer'},
        title="Vehicle Count by Manufacturer"
    )
    fig_mfg.update_layout(height=500)
    st.plotly_chart(fig_mfg, use_container_width=True)
    
    # Trend over years
    if len(selected_years) > 1 or not selected_years:
        st.subheader("Vehicle Count Over Years")
        year_counts = filtered_df.groupby('Year').size().reset_index(name='Count')
        fig_trend = px.line(
            year_counts,
            x='Year',
            y='Count',
            markers=True,
            title="Vehicle Models per Year"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

with tab2:
    st.header("Assembly Locations")
    
    # Assembly country distribution
    assembly_counts = filtered_df['Assembly Country'].value_counts().head(20)
    
    st.subheader("Top Assembly Countries")
    
    # Create bar chart with flags
    fig_assembly = go.Figure()
    fig_assembly.add_trace(go.Bar(
        x=assembly_counts.values,
        y=[f"{get_flag(country)} {country}" for country in assembly_counts.index],
        orientation='h',
        marker=dict(color='lightblue')
    ))
    fig_assembly.update_layout(
        xaxis_title="Number of Vehicles",
        yaxis_title="Assembly Country",
        height=600
    )
    st.plotly_chart(fig_assembly, use_container_width=True)

with tab3:
    st.header("Component Origins")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Engine Source Countries")
        engine_counts = filtered_df['Engine Source'].value_counts().head(15)
        fig_engine = px.pie(
            values=engine_counts.values,
            names=[f"{get_flag(c)} {c}" for c in engine_counts.index],
            title="Engine Sources"
        )
        st.plotly_chart(fig_engine, use_container_width=True)
    
    with col2:
        st.subheader("Transmission Source Countries")
        trans_counts = filtered_df['Transmission Source'].value_counts().head(15)
        fig_trans = px.pie(
            values=trans_counts.values,
            names=[f"{get_flag(c)} {c}" for c in trans_counts.index],
            title="Transmission Sources"
        )
        st.plotly_chart(fig_trans, use_container_width=True)

with tab4:
    st.header("Content Percentages by Country")
    st.markdown("""
    This view shows the percentage of vehicle content sourced from different countries.
    The **US/Canada Content** represents parts from North America, while **Primary** and **Secondary** countries 
    show the main foreign sources of parts.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # US/Canada Content Distribution
        st.subheader("🇺🇸🇨🇦 US/Canada Content Distribution")
        
        # Create bins for US/Canada percentage
        if '% US/Canada' in filtered_df.columns:
            bins = [0, 10, 25, 50, 75, 100]
            labels = ['0-10%', '10-25%', '25-50%', '50-75%', '75-100%']
            filtered_df['Content Bin'] = pd.cut(
                filtered_df['% US/Canada'], 
                bins=bins, 
                labels=labels, 
                include_lowest=True
            )
            bin_counts = filtered_df['Content Bin'].value_counts().sort_index()
            
            fig_bins = px.bar(
                x=bin_counts.index.astype(str),
                y=bin_counts.values,
                labels={'x': 'US/Canada Content %', 'y': 'Number of Vehicles'},
                title="Vehicles by US/Canada Content Level",
                color=bin_counts.values,
                color_continuous_scale='RdYlGn'
            )
            fig_bins.update_layout(showlegend=False)
            st.plotly_chart(fig_bins, use_container_width=True)
    
    with col2:
        # Average US/Canada content by manufacturer
        st.subheader("Average US/Canada Content by Manufacturer")
        
        if '% US/Canada' in filtered_df.columns:
            avg_content = filtered_df.groupby('Manufacturer')['% US/Canada'].mean().sort_values(ascending=True)
            avg_content = avg_content.tail(15)  # Top 15
            
            fig_avg = px.bar(
                x=avg_content.values,
                y=avg_content.index,
                orientation='h',
                labels={'x': 'Average % US/Canada', 'y': 'Manufacturer'},
                title="Top 15 Manufacturers by US/Canada Content",
                color=avg_content.values,
                color_continuous_scale='RdYlGn'
            )
            fig_avg.update_layout(showlegend=False)
            st.plotly_chart(fig_avg, use_container_width=True)
    
    # Primary source countries
    st.subheader("🌍 Primary Source Countries (Excluding US/Canada)")
    
    if 'Primary Country' in filtered_df.columns:
        # Get primary country contributions
        primary_data = filtered_df[filtered_df['Primary Country'].notna() & (filtered_df['Primary Country'] != '')]
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Count of vehicles by primary country
            primary_counts = primary_data['Primary Country'].value_counts().head(15)
            
            fig_primary = go.Figure()
            fig_primary.add_trace(go.Bar(
                x=primary_counts.values,
                y=[f"{get_flag(c)} {c}" for c in primary_counts.index],
                orientation='h',
                marker=dict(color='steelblue')
            ))
            fig_primary.update_layout(
                title="Vehicles by Primary Source Country",
                xaxis_title="Number of Vehicles",
                yaxis_title="Country",
                height=500
            )
            st.plotly_chart(fig_primary, use_container_width=True)
        
        with col4:
            # Average percentage by primary country
            if 'Primary %' in filtered_df.columns:
                avg_primary = primary_data.groupby('Primary Country')['Primary %'].mean().sort_values(ascending=False).head(15)
                
                fig_avg_primary = go.Figure()
                fig_avg_primary.add_trace(go.Bar(
                    x=[f"{get_flag(c)} {c}" for c in avg_primary.index],
                    y=avg_primary.values,
                    marker=dict(color='coral')
                ))
                fig_avg_primary.update_layout(
                    title="Average Content % by Primary Country",
                    xaxis_title="Country",
                    yaxis_title="Average %",
                    height=500
                )
                fig_avg_primary.update_xaxes(tickangle=45)
                st.plotly_chart(fig_avg_primary, use_container_width=True)
    
    # Content breakdown for selected manufacturer
    st.subheader("📊 Content Breakdown by Manufacturer")
    
    if selected_manufacturers and len(selected_manufacturers) == 1:
        mfg = selected_manufacturers[0]
        mfg_data = filtered_df[filtered_df['Manufacturer'] == mfg]
        
        # Calculate average content sources
        avg_us_canada = mfg_data['% US/Canada'].mean() if '% US/Canada' in mfg_data.columns else 0
        avg_primary = mfg_data['Primary %'].mean() if 'Primary %' in mfg_data.columns else 0
        avg_secondary = mfg_data['Secondary %'].mean() if 'Secondary %' in mfg_data.columns else 0
        other = max(0, 100 - avg_us_canada - avg_primary - avg_secondary)
        
        # Get most common primary country
        primary_country = mfg_data['Primary Country'].mode().iloc[0] if len(mfg_data['Primary Country'].mode()) > 0 else "Other"
        
        fig_pie = px.pie(
            values=[avg_us_canada, avg_primary, avg_secondary, other],
            names=[f'🇺🇸🇨🇦 US/Canada ({avg_us_canada:.1f}%)', 
                   f'{get_flag(primary_country)} {primary_country} ({avg_primary:.1f}%)',
                   f'Secondary ({avg_secondary:.1f}%)',
                   f'Other ({other:.1f}%)'],
            title=f"Average Content Sources for {mfg}",
            color_discrete_sequence=['#2ecc71', '#3498db', '#9b59b6', '#95a5a6']
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Select a single manufacturer from the sidebar to see detailed content breakdown.")

with tab5:
    st.header("Data Table")
    
    # Display columns
    display_cols = ['Year', 'Manufacturer', 'Car Line', '% US/Canada',
                   'Primary Country', 'Primary %', 'Secondary Country', 'Secondary %',
                   'Engine Source', 'Transmission Source', 'Assembly Country']
    
    # Filter to only existing columns
    display_cols = [col for col in display_cols if col in filtered_df.columns]
    
    # Add flags to countries in the table
    display_df = filtered_df[display_cols].copy()
    
    if 'Assembly Country' in display_df.columns:
        display_df['Assembly Country'] = display_df['Assembly Country'].apply(
            lambda x: f"{get_flag(x)} {x}" if pd.notna(x) else ""
        )
    
    if 'Engine Source' in display_df.columns:
        display_df['Engine Source'] = display_df['Engine Source'].apply(
            lambda x: f"{get_flag(x)} {x}" if pd.notna(x) else ""
        )
    
    if 'Transmission Source' in display_df.columns:
        display_df['Transmission Source'] = display_df['Transmission Source'].apply(
            lambda x: f"{get_flag(x)} {x}" if pd.notna(x) else ""
        )
    
    if 'Primary Country' in display_df.columns:
        display_df['Primary Country'] = display_df['Primary Country'].apply(
            lambda x: f"{get_flag(x)} {x}" if pd.notna(x) and x != "" else ""
        )
    
    if 'Secondary Country' in display_df.columns:
        display_df['Secondary Country'] = display_df['Secondary Country'].apply(
            lambda x: f"{get_flag(x)} {x}" if pd.notna(x) and x != "" else ""
        )
    
    st.dataframe(display_df, use_container_width=True, height=600)
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name="nhtsa_filtered_data.csv",
        mime="text/csv",
    )

# Footer
st.markdown("---")
st.markdown("""
**Data Source:** [NHTSA Part 583 American Automobile Labeling Act Reports](https://www.nhtsa.gov/part-583-american-automobile-labeling-act-reports)

**Note:** Country codes have been normalized (e.g., MEX/MX → Mexico). Some ambiguous codes like "CH" have been interpreted based on context.
""")
