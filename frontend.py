import streamlit as st
import tempfile
import subprocess
import json
import os

from analyze.scrapper import fetch_and_save_esg
from analyze.getting_accuracy import evaluate_themes

st.logo(
    "🌿"
)
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

    company_name = company_name_input  # will override later if needed

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
                subprocess.run(
                    ["python", "claims_extractor/run_pdf_claims_extractor.py", temp_pdf_path],
                    check=True
                )
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
        try:
            fetch_and_save_esg(company_name)
            st.success("Company ESG data fetched ✅")
        except Exception as e:
            st.error(f"ESG Fetch Error: {e}")

        # Evaluate themes
        try:
            evaluate_themes(
                input_path="claimtoclassify/theme_summaries.json",
                output_path="analyze/theme_summaries_with_scores.json"
            )
            st.success("Theme evaluation completed ✅")
        except Exception as e:
            st.error(f"Theme Evaluation Error: {e}")

        # Save last analyzed company
        meta_data = {
            "last_analyzed_company": company_name
        }

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
    # LOAD JSON DATA
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

    # ============================================================
    # LANGUAGE ANALYSIS
    # ============================================================
    st.subheader("📖 Language Analysis")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Vague Words Score",
        f"{vague['vague_words_score']}/100"
    )

    col2.metric(
        "Vague Density",
        f"{vague['vague_density']*100:.2f}%"
    )

    col3.metric(
        "Readability Difficulty",
        f"{difficulty['difficulty_to_read_score']}/100"
    )

    col4.metric(
        "Flesch Reading Ease",
        f"{difficulty['flesch_reading_ease']}"
    )

    st.markdown("### 📊 Score Breakdown")

    st.write("**Vague Language Risk**")
    st.progress(vague["vague_words_score"] / 100)

    st.write("**Reading Difficulty Level**")
    st.progress(difficulty["difficulty_to_read_score"] / 100)

    with st.expander("🔍 Know About Language Analysis"):
        st.markdown(
            """
            - **Vague Words Score**: Measures the density of vague and ambiguous terms. Higher scores indicate more vague language, which can undermine credibility.
            - **Vague Density**: The percentage of words that are considered vague. A lower percentage is generally better.
            - **Readability Difficulty**: Assesses how difficult the text is to read. Higher scores indicate more complex language, which may not be accessible to all audiences.
            - **Flesch Reading Ease**: A standard readability metric where higher scores indicate easier-to-read text. Scores above 60 are generally considered good for public-facing content.
            """
        )



    # ============================================================
    # CLAIM ANALYSIS
    # ============================================================
    st.subheader("📊 Claim Analysis")

    total_claims = len(claims)

    avg_assertiveness = round(
        sum(c["assertiveness_score"] for c in claims) / total_claims,
        3
    )

    claim_type_distribution = {
        "performance": 0,
        "future": 0,
        "qualitative": 0
    }

    for c in claims:
        claim_type_distribution[c["claim_type"]] += 1

    col3, col4 = st.columns(2)

    with col3:
        st.metric("Average Assertiveness", f"{avg_assertiveness * 100:.1f}%")

    with col4:
        st.metric("Total Claims", total_claims)

    st.markdown("#### Claim Type Distribution")
    st.bar_chart(claim_type_distribution, horizontal=True, height=200)

    with st.expander("🔍 Know About Claim Analysis"):
        st.markdown(
            """
            - **Average Assertiveness**: Indicates how confidently the claims are stated. Higher scores suggest more definitive language, while lower scores may indicate hedging or uncertainty.
            - **Claim Type Distribution**: Shows the breakdown of claims into categories such as performance (current achievements), future (aspirational goals), and qualitative (descriptive statements). A balanced distribution can indicate a well-rounded report, while a heavy skew towards future claims may suggest a focus on aspirations rather than current performance.
            """
        )

    # ============================================================
    # COMPANY PROFILE
    # ============================================================
    st.subheader("🏢 Company Profile")

    selected_company = company_data.get(company_name)

    if selected_company:

        colA, colB = st.columns(2)

        with colA:
            st.metric("ESG Rating", selected_company.get("ESG_rating", "N/A"))
            st.metric("CDP Score", selected_company.get("CDP_score", "N/A"))

        with colB:
            st.markdown("#### 🌍 Carbon Footprint")
            carbon = selected_company.get("carbon_footprint", {})
            st.write(f"Year: {carbon.get('year', 'N/A')}")
            st.write(f"Scope 1: {carbon.get('scope1', 'N/A')}")
            st.write(f"Scope 2: {carbon.get('scope2', 'N/A')}")
            st.write(f"Scope 3: {carbon.get('scope3', 'N/A')}")

        st.markdown("#### 🎯 Top 3 ESG Commitments")
        for promise in selected_company.get("top3_commitments", []):
            st.write(f"- {promise}")

    else:
        st.warning(f"Company '{company_name}' not found in company_data.json")

    with st.expander("🔍 Know About Company Profile"):
        st.markdown(
            """
            - **ESG Rating**: A score that evaluates the company's overall performance in environmental, social, and governance factors. Higher ratings indicate better ESG practices.
            - **CDP Score**: A score provided by the Carbon Disclosure Project that assesses a company's environmental impact and transparency. Higher scores reflect better environmental performance and disclosure.
            - **Carbon Footprint**: The total greenhouse gas emissions caused directly and indirectly by the company, typically measured in metric tons of CO2 equivalent. Scope 1 covers direct emissions from owned or controlled sources, Scope 2 covers indirect emissions from the generation of purchased energy, and Scope 3 includes all other indirect emissions that occur in the value chain.
            - **Top ESG Commitments**: Key promises or goals that the company has publicly stated regarding its ESG initiatives. These commitments can provide insight into the company's priorities and future plans.
            """
        )

    # ============================================================
    # THEME ACCURACY
    # ============================================================
    st.subheader("🎯 Theme Accuracy")

    theme_scores = {
        theme_name: data["theme_score"]
        for theme_name, data in theme_summaries.items()
    }

    st.bar_chart(theme_scores, horizontal=True, height=250)

    # ============================================================
    # THEME INSIGHTS
    # ============================================================
    st.subheader("📝 Theme Insights")

    for theme_name, data in theme_summaries.items():
        with st.expander(
            f"{theme_name}  |  Claim Density: {data['claim_density_percent']}%"
        ):
            for point in data["theme_summary"]:
                st.markdown(f"- {point}")

    with st.expander("🔍 Know About Theme Insights"):
        st.markdown(
            """
            - **Theme Accuracy**: Evaluates how well the claims in the report align with the company's stated ESG commitments and performance. Higher scores indicate better alignment and credibility.
            - **Claim Density**: The percentage of claims that are related to each specific theme. A higher density can indicate a stronger focus on that theme, while a lower density may suggest it is less emphasized in the report.
            - **Theme Insights**: Key takeaways and observations about each theme based on the claims made in the report. These insights can help identify strengths, weaknesses, and areas for improvement in the company's ESG reporting.
            """
        )