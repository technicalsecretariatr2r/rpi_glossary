import streamlit as st
import pandas as pd
import os
from fuzzywuzzy import fuzz

# Configure page settings to align with RPI branding
st.set_page_config(
    page_title="Resilience Planet Initiative Glossary",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and introduction reflecting updated narrative
st.title("Resilience Planet Initiative Glossary")
st.markdown("""
Welcome to the Resilience Planet Initiative Glossary App.  
This application offers a friendly way to explore a wide range of definitions and classifications that underpin how solutions could be organized within the RPI ecosystem.  
It is designed to facilitate access to these key definitions during the design process of the Solution Hub.

Use the sidebar to filter entries by their classification system (Source) and the search tools below to quickly find the definitions and concepts.
""")



# Function to load the glossary data
@st.cache_data
def load_glossary(sheet_name="Sheet1"):
    file_path_glossary = "RPI_glossary_official_info.xlsx"
    if not os.path.exists(file_path_glossary):
        st.error(f"The file '{file_path_glossary}' was not found. Please ensure it is uploaded in the repository.")
        st.stop()
    return pd.read_excel(file_path_glossary, sheet_name=sheet_name)

# Load the glossary using the "Glossary" sheet
df_glossary = load_glossary(sheet_name="Glossary")

# Sidebar: Filter Options using the Source variable as a classification system
st.sidebar.header("Filters")
sources = sorted(df_glossary["Source"].dropna().unique())
selected_source = st.sidebar.radio("Filter by Classification System:", options=["All Sources"] + sources, index=0)

# Apply filter based on the selected classification system
df_filtered = df_glossary if selected_source == "All Sources" else df_glossary[df_glossary["Source"] == selected_source]

# Advanced Search Section with Autocomplete suggestions
st.markdown("### Advanced Search")
operador = st.selectbox("Logical Operator:", options=["AND", "OR"], index=0)

if "search_query_default" not in st.session_state:
    st.session_state["search_query_default"] = ""

search_query = st.text_input("Enter search term(s):", value=st.session_state["search_query_default"], key="search_query")

def get_suggestions(query, df):
    suggestions = set()
    if query:
        for txt in df["Definition"].dropna():
            for word in str(txt).split():
                if word.lower().startswith(query.lower()):
                    suggestions.add(word)
    return sorted(suggestions)[:5]

sugerencias = get_suggestions(search_query, df_filtered)
if sugerencias:
    st.markdown("**Suggestions:**")
    for sug in sugerencias:
        if st.button(sug, key=f"sugg_{sug}"):
            st.session_state["search_query_default"] = sug
            st.experimental_rerun()

# Fuzzy Search Function: Matches rows based on search terms and logical operator
def match_row(row, terms, operador="AND", threshold=70):
    combined_text = " ".join([str(row[col]) for col in ["Source", "Definition", "Category", "Code"] if col in row and pd.notnull(row[col])]).lower()
    if operador == "AND":
        return all(fuzz.partial_ratio(t.lower(), combined_text) >= threshold for t in terms)
    else:
        return any(fuzz.partial_ratio(t.lower(), combined_text) >= threshold for t in terms)

# Process Search Query
terms = [t.strip() for t in search_query.split() if t.strip()]
df_search_results = df_filtered[df_filtered.apply(lambda row: match_row(row, terms, operador), axis=1)] if terms else df_filtered

# Displaying the results
st.subheader("Glossary Search Results")
if df_search_results.empty:
    st.write("No results found. Try adjusting your filters or search terms.")
else:
    for _, row in df_search_results.iterrows():
        # Create a link if a URL is available
        link_html = f" | <a href='{row['Link']}' target='_blank'>Learn more</a>" if pd.notnull(row['Link']) else ""
        st.markdown(
            f"""
            <div style="padding: 15px; background-color: #f9f9f9; border-left: 7px solid #8AB2A6; margin-bottom: 15px;">
                <div style="font-size: 20px; font-weight: bold; color: #333;">
                    {row['Category']}
                </div>
                <div style="font-size: 20px; margin-top: 10px; color: #555;">
                    {row['Definition']}
                </div>
                <div style="font-size: 14px; margin-top: 10px; color: #777;">
                    <strong>Classification System:</strong> {row['Source']}
                    {link_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

    if st.checkbox("Show full data table", key="full_table_filtered"):
        st.dataframe(df_search_results)
