import pandas as pd
import streamlit as st
import tempfile
import subprocess
import json
import os
import re

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def clean_carbon_value(val):
    """Removes 'tCO2e', commas, and other text to return a clean float."""
    if pd.isna(val) or val == "N/A" or val is None:
        return None
    clean_str = re.sub(r'[^\d.]', '', str(val))
    try:
        return float(clean_str)
    except ValueError:
        return None

# -----------------------------
# RATING HELPERS
# -----------------------------
MSCI_RANKS = {"AAA": 7, "AA": 6, "A": 5, "BBB": 4, "BB": 3, "B": 2, "CCC": 1, "N/A": 0}

def convert_score_to_msci(score):
    """Converts a numerical CSV score (0-1) to an MSCI letter grade."""
    if score is None or pd.isna(score): return "N/A"
    if score >= 0.85: return "AAA"
    if score >= 0.71: return "AA"
    if score >= 0.57: return "A"
    if score >= 0.43: return "BBB"
    if score >= 0.29: return "BB"
    if score >= 0.14: return "B"
    return "CCC"
def calc_pct_diff(comp_val, avg_val):
    """Calculates the percentage difference and returns a formatted string."""
    if comp_val is None or avg_val is None or avg_val == 0 or pd.isna(avg_val):
        return "N/A"
    diff = ((comp_val - avg_val) / avg_val) * 100
    if diff > 0:
        return f"+{diff:.1f}% 🔺"
    elif diff < 0:
        return f"{diff:.1f}% 🔻"
    else:
        return "0.0%"

@st.cache_data
def load_csv_dataset():
    """Loads the benchmark dataset."""
    try:
        return pd.read_csv("data/company_dataset.csv")
    except Exception:
        return pd.DataFrame()

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.logo("🌿")
st.set_page_config(page_title="ESG Claim Analyzer", layout="wide")
st.title("ESG - Environmental Analysis Dashboard")

company_name_input = st.text_input("Company Name")
uploaded_file = st.file_uploader("Upload Sustainability Report (PDF)", type="pdf")

# -----------------------------
# TOGGLE MODE
# -----------------------------
mode = st.radio(
    "Select Mode",
    ("Run Full Analysis", "Use Pre-existing JSON Data")
)

# -----------------------------
# PROCESS BUTTON
# -----------------------------
if st.button("Process", type="primary"):

    company_name = company_name_input 

    # ============================================================
    # MODE 1: RUN FULL ANALYSIS
    # ============================================================
    if mode == "Run Full Analysis":

        if not uploaded_file:
            st.error("Please upload a PDF file.")
            st.stop()

        if not company_name:
            st.error("Please enter a company name.")
            st.stop()

        with st.spinner("Processing PDF..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                temp_pdf_path = tmp.name

            try:
                subprocess.run(["python", "claims_extractor/run_pdf_claims_extractor.py", temp_pdf_path], check=True)
                subprocess.run(["python", "claim_scorer/assertiveness.py"], check=True)
                subprocess.run(["python", "claimtoclassify/sum_class.py"], check=True)
                subprocess.run(["python", "claimtoclassify/summarizer_to_claims.py"], check=True)
                st.success("PDF Analysis Completed ✅")
            except Exception as e:
                st.error(f"PDF Analysis Error: {e}")
                st.stop()
            finally:
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)

        # Fetch ESG data
        from analyze.scrapper import fetch_and_save_esg
        try:
            fetch_and_save_esg(company_name)
            st.success("Company ESG data fetched ✅")
        except Exception as e:
            st.error(f"ESG Fetch Error: {e}")

        # Evaluate themes
        from analyze.getting_accuracy import evaluate_themes
        try:
            evaluate_themes(
                input_path="claimtoclassify/theme_summaries.json",
                output_path="analyze/theme_summaries_with_scores.json"
            )
            st.success("Theme evaluation completed ✅")
        except Exception as e:
            st.error(f"Theme Evaluation Error: {e}")

        # Save last analyzed company
        meta_data = {"last_analyzed_company": company_name}
        os.makedirs("analyze", exist_ok=True)
        with open("analyze/session_meta.json", "w") as f:
            json.dump(meta_data, f)

    # ============================================================
    # MODE 2: USE PRE-EXISTING JSON
    # ============================================================
    else:
        try:
            with open("analyze/session_meta.json") as f:
                meta = json.load(f)
                company_name = meta.get("last_analyzed_company")
                st.info(f"Using previously analyzed company: {company_name}")
        except Exception:
            st.error("No previous analysis found.")
            st.stop()

    # ============================================================
    # LOAD JSON DATA & CSV BENCHMARKS
    # ============================================================
    try:
        with open("claims_extractor/scores.json") as f:
            scores = json.load(f)
            vague = scores["vague_words_score"]
            difficulty = scores["difficulty_score"]

        with open("claim_scorer/claims_with_scores.json") as f:
            claims = json.load(f)

        with open("analyze/company_data.json") as f:
            company_data = json.load(f)

        with open("analyze/theme_summaries_with_scores.json") as f:
            theme_summaries = json.load(f)
            
    except Exception as e:
        st.error(f"Failed to load JSON data: {e}")
        st.stop()

    df_csv = load_csv_dataset()
    avg_label = "Dataset Avg"
    
    if not df_csv.empty:
        if company_name in df_csv["Company"].values:
            sector = df_csv.loc[df_csv["Company"] == company_name, "Sector"].values[0]
            benchmark_df = df_csv[df_csv["Sector"] == sector]
            avg_label = f"{sector} Sector Avg"
        else:
            benchmark_df = df_csv
            
        avg_vague = benchmark_df["Vague"].mean() * 100 
        avg_readability = benchmark_df["Readability"].mean() * 100
        avg_assertiveness_csv = benchmark_df["Assertiveness"].mean()
        avg_scope1 = benchmark_df["Scope1"].mean()
        avg_scope2 = benchmark_df["Scope2"].mean()
        avg_scope3 = benchmark_df["Scope3"].mean()
        avg_msci = benchmark_df["MSCI"].mean()
    else:
        avg_vague = avg_readability = avg_assertiveness_csv = 0
        avg_scope1 = avg_scope2 = avg_scope3 = 0

    # ============================================================
    # LANGUAGE ANALYSIS
    # ============================================================
    st.subheader("📖 Language Analysis")
    col1, col2, col3, col4 = st.columns(4)
    
    v_score = vague['vague_words_score']
    v_delta = v_score - avg_vague if not df_csv.empty else None

    col1.metric("Vague Words Score", f"{v_score}/100", delta=f"{v_delta:.1f} vs {avg_label}" if v_delta is not None else None, delta_color="inverse")
    col2.metric("Vague Density", f"{vague['vague_density']*100:.2f}%")

    d_score = difficulty['difficulty_to_read_score']
    d_delta = d_score - avg_readability if not df_csv.empty else None

    col3.metric("Readability Difficulty", f"{d_score}/100", delta=f"{d_delta:.1f} vs {avg_label}" if d_delta is not None else None, delta_color="inverse")
    col4.metric("Flesch Reading Ease", f"{difficulty['flesch_reading_ease']}")

    st.markdown("### 📊 Score Breakdown")
    st.write("**Vague Language Risk**")
    st.progress(vague["vague_words_score"] / 100)
    st.write("**Reading Difficulty Level**")
    st.progress(difficulty["difficulty_to_read_score"] / 100)

    # ============================================================
    # CLAIM ANALYSIS
    # ============================================================
    st.subheader("📊 Claim Analysis")
    total_claims = len(claims)
    avg_assertiveness = round(sum(c["assertiveness_score"] for c in claims) / total_claims, 3) if total_claims > 0 else 0

    claim_type_distribution = {"performance": 0, "future": 0, "qualitative": 0}
    for c in claims:
        claim_type_distribution[c.get("claim_type", "qualitative")] += 1

    col3, col4 = st.columns(2)
    a_delta = (avg_assertiveness - avg_assertiveness_csv) * 100 if not df_csv.empty else None

    with col3:
        st.metric("Average Assertiveness", f"{avg_assertiveness * 100:.1f}%", delta=f"{a_delta:.1f}% vs {avg_label}" if a_delta is not None else None, delta_color="normal")
    with col4:
        st.metric("Total Claims", total_claims)

    st.markdown("#### Claim Type Distribution")
    st.bar_chart(claim_type_distribution, horizontal=True, height=200)

# ============================================================
    # COMPANY PROFILE
    # ============================================================
    st.subheader("🏢 Company Profile")
    selected_company = company_data.get(company_name)

    if selected_company:
        colA, colB = st.columns([1, 2])

        with colA:
            # 1. Clean the rating by splitting at the parenthesis
            raw_rating = selected_company.get("ESG_rating", "N/A")
            clean_rating = raw_rating.split("(")[0].strip() if "(" in raw_rating else raw_rating
            
            st.metric("ESG Rating", clean_rating)
            st.metric("CDP Score", selected_company.get("CDP_score", "N/A"))

            # 2. Rating Comparison Logic
            if clean_rating in MSCI_RANKS and not df_csv.empty:
                avg_msci_rating = convert_score_to_msci(avg_msci)
                comp_rank = MSCI_RANKS.get(clean_rating, 0)
                avg_rank = MSCI_RANKS.get(avg_msci_rating, 0)
                
                st.markdown("#### ⚖️ MSCI Comparison")
                if comp_rank > avg_rank:
                    st.success(f"**Good!** Rated higher than the {avg_label} ({avg_msci_rating}).")
                elif comp_rank < avg_rank:
                    st.error(f"**Rated Less!** Below the {avg_label} ({avg_msci_rating}).")
                else:
                    st.info(f"**Average.** On par with the {avg_label} ({avg_msci_rating}).")
            
            st.divider()


        with colB:
            st.markdown(f"#### 🌍 Carbon Footprint Comparison ({avg_label})")
            carbon = selected_company.get("carbon_footprint", {})

            if carbon:
                c_scope1 = clean_carbon_value(carbon.get("scope1"))
                c_scope2 = clean_carbon_value(carbon.get("scope2"))
                c_scope3 = clean_carbon_value(carbon.get("scope3"))

                df_carbon = pd.DataFrame({
                    "Metric": ["Scope 1", "Scope 2", "Scope 3"],
                    "Company (tCO2e)": [
                        f"{c_scope1:,.0f}" if c_scope1 is not None else "N/A",
                        f"{c_scope2:,.0f}" if c_scope2 is not None else "N/A",
                        f"{c_scope3:,.0f}" if c_scope3 is not None else "N/A"
                    ],
                    f"Avg ({avg_label})": [
                        f"{avg_scope1:,.0f}" if not df_csv.empty else "N/A",
                        f"{avg_scope2:,.0f}" if not df_csv.empty else "N/A",
                        f"{avg_scope3:,.0f}" if not df_csv.empty else "N/A"
                    ],
                    "% vs Average": [
                        calc_pct_diff(c_scope1, avg_scope1),
                        calc_pct_diff(c_scope2, avg_scope2),
                        calc_pct_diff(c_scope3, avg_scope3)
                    ]
                })
                st.table(df_carbon)
            else:
                st.write("No carbon footprint data available.")
            
            st.markdown("#### 🎯 Top 3 ESG Commitments")
            commitments = selected_company.get("top3_commitments", [])
            if commitments:
                df_commitments = pd.DataFrame({"Commitment #": [f"{i+1}" for i in range(len(commitments))], "Commitment": commitments})
                st.table(df_commitments)
            else:
                st.write("No commitments available.")
    else:
        st.warning(f"Company '{company_name}' not found in company_data.json")
# ============================================================
    # CLAIM ACCURACY & RISK SCORING
    # ============================================================
    st.subheader("🎯 Claim Accuracy & Risk Scoring")

    # -----------------------------------------
    # PRE-COMPUTE THEME ACCURACY 
    # (Calculated first so the Risk algorithm can use it)
    # -----------------------------------------
    theme_chart_data = {
        "Theme": [],
        "Company Score": [],
        f"{avg_label}": []
    }

    theme_to_csv_map = {
        "climate change & net zero": "Climate",
        "energy & renewables": "Energy",
        "ghg emissions": "GHG",
        "biodiversity & natural capital": "Biodiversity",
        "waste & circularity": "Waste",
        "water & effluents": "Water",
        "other environmental": "OtherEnv"
    }

    comp_total, avg_total, theme_count = 0, 0, 0

    for theme_name, data in theme_summaries.items():
        raw_comp_score = data["theme_score"]
        
        # 🚨 THE FIX: If the score is a decimal like 0.8, multiply by 100 to make it 80
        comp_score = raw_comp_score * 100 if raw_comp_score <= 1.0 else raw_comp_score
        
        avg_score = 0
        
        if not df_csv.empty:
            match_col = None
            theme_lower = theme_name.lower()
            
            # Try explicit mapping
            for key, val in theme_to_csv_map.items():
                if key in theme_lower:
                    match_col = val
                    break
            
            # Fallback mapping
            if not match_col:
                ignore_cols = ["Company", "Sector", "Vague", "Assertiveness", "Readability", "Scope1", "Scope2", "Scope3", "MSCI"]
                for col in df_csv.columns:
                    if col not in ignore_cols and (col.lower() in theme_lower or theme_lower in col.lower()):
                        match_col = col
                        break
            
            if match_col and match_col in df_csv.columns:
                # Replace 0 with NaN temporarily so it isn't factored into the average
                raw_avg = benchmark_df[match_col].replace(0, pd.NA).mean()
                
                # 🚨 THE FIX: Ensure the CSV average is also scaled to 100
                avg_score = raw_avg * 100 if raw_avg <= 1.0 else raw_avg

        theme_chart_data["Theme"].append(theme_name)
        theme_chart_data["Company Score"].append(comp_score)
        theme_chart_data[f"{avg_label}"].append(avg_score if avg_score > 0 else 0)
        
        comp_total += comp_score
        avg_total += avg_score
        theme_count += 1
    # Get the overall accuracy score for the Risk Index
    overall_comp = (comp_total / theme_count) if theme_count > 0 else 100 # Defaults to 100 if no data
    # -----------------------------------------
    # ROW 2: THEME ACCURACY CHART (Full Width)
    # -----------------------------------------
    st.markdown(f"#### 📊 Theme Accuracy vs {avg_label}")

    # Calculate Overall Composite Score for the subheader
    if theme_count > 0:
        overall_avg = avg_total / theme_count
        delta_val = overall_comp - overall_avg
        
        st.metric("Overall Composite Accuracy", f"{overall_comp:.1f}/100", delta=f"{delta_val:.1f} vs {avg_label}" if not df_csv.empty else None)

    # Plot side-by-side chart
    df_theme_chart = pd.DataFrame(theme_chart_data).set_index("Theme")
    st.bar_chart(df_theme_chart, horizontal=True, stack=False, height=350)

    # ============================================================
    # THEME INSIGHTS
    # ============================================================
    st.subheader("📝 Theme Insights")

    for theme_name, data in theme_summaries.items():
        with st.expander(f"{theme_name}  |  Claim Density: {data['claim_density_percent']}%"):
            for point in data["theme_summary"]:
                st.markdown(f"- {point}")


    # -----------------------------------------
    # ROW 1: GREENWASHING RISK INDEX (Full Width)
    # -----------------------------------------
    st.markdown("#### 🚨 Greenwashing Risk Index")
    
    selected_company = company_data.get(company_name, {})
    carbon_data = selected_company.get("carbon_footprint", {})
    
    # 1. Grab NLP Scores
    v_score = vague.get('vague_words_score', 0)
    r_score = difficulty.get('difficulty_to_read_score', 0)
    
    # 2. Calculate Scope 3 Percentage safely
    s1 = clean_carbon_value(carbon_data.get("scope1")) or 0
    s2 = clean_carbon_value(carbon_data.get("scope2")) or 0
    s3 = clean_carbon_value(carbon_data.get("scope3")) or 0
    
    total_carbon = s1 + s2 + s3
    scope3_pct = (s3 / total_carbon * 100) if total_carbon > 0 else 100 
        
    # 3. Apply Custom Weights (Now incorporates Theme Inaccuracy)
    weight_vague = (v_score / 100) * 30
    weight_readability = (r_score / 100) * 25
    weight_scope3 = ((100 - scope3_pct) / 100) * 25  # Low Scope 3 = High Risk Penalty
    weight_inaccuracy = ((100 - overall_comp) / 100) * 20 # Low accuracy = High Risk Penalty
    
    # 4. Calculate Final Score
    gw_score = round(weight_vague + weight_readability + weight_scope3 + weight_inaccuracy, 1)
    
    if gw_score >= 66:
        gw_category = "SEVERE RISK 🛑"
        gw_color = "red"
    elif gw_score >= 36:
        gw_category = "MODERATE RISK ⚠️"
        gw_color = "orange"
    else:
        gw_category = "LOW RISK ✅"
        gw_color = "green"

    # Display Gauge & Progress
    st.markdown(f"<h1 style='text-align: center; color: {gw_color}; margin-bottom: 0;'>{gw_score} / 100</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: {gw_color}; margin-top: 0;'>{gw_category}</h4>", unsafe_allow_html=True)
    st.progress(gw_score / 100)
    
    with st.expander("📊 View Risk Methodology"):
        st.write(f"**Vagueness Penalty (30%):** +{round(weight_vague, 1)} pts")
        st.write(f"**Obfuscation Penalty (25%):** +{round(weight_readability, 1)} pts")
        st.write(f"**Scope 3 Anomaly (25%):** +{round(weight_scope3, 1)} pts")
        st.write(f"**Theme Inaccuracy Penalty (20%):** +{round(weight_inaccuracy, 1)} pts")
        st.caption(f"Company reported an Overall Theme Accuracy of {overall_comp:.1f}% and a Scope 3 ratio of {scope3_pct:.1f}%. Lower accuracy and lower supply-chain reporting mathematically increase the greenwashing risk.")

    st.divider()

