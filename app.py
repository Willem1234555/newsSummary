import os
from functools import partial

import streamlit as st

# --- Local helpers -----------------------------------------------------------
from generateIndustrySummary import (
    get_industry_summary_openai,
    get_industry_summary_gemini,
    get_industry_summary_r1_1776,
    get_industry_summary_perplexity,
)

st.set_page_config(page_title="Sector News Overview", layout="wide")

st.title("Sector News Overview")

# -----------------------------------------------------------------------------
# Sidebar – all user‑tweakable parameters
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("Parameters")

    # Core business inputs
    client_company = st.text_input("Client company", "ING")
    client_industry = st.text_input("Client industry", "Banking / Finance")
    search_query = st.text_area(
        "Search query",
        "bank OR banken OR bankieren OR economie OR rente OR ABN‑AMRO OR Rabobank",
    )
    lang = st.selectbox("Language", ["nl-NL", "en-US"], index=0)
    country = st.text_input("Country code", "NL")

    # One multiselect for **all** models
    model_options = {
        "OpenAI: gpt-4o": ("openai", "gpt-4o"),
        "OpenAI: o4-mini": ("openai", "o4-mini"),
        "OpenAI: gpt-4o-mini": ("openai", "gpt-4o-mini"),
        "Gemini: gemini-2.0-flash": ("gemini", "gemini-2.0-flash"),
        "Perplexity: r1-1776": ("perplexity_r1", "r1-1776"),
        "Perplexity: sonar-pro": ("perplexity_sonar", "sonar-pro"),
    }

    default_selection = [
        "OpenAI: gpt-4o",
        "OpenAI: o4-mini",
        "Gemini: gemini-2.0-flash",
        "Perplexity: r1-1776",
        "Perplexity: sonar-pro",
    ]

    selected_labels = st.multiselect(
        "Models to run (multi-select)",
        list(model_options.keys()),
        default=default_selection,
    )

    # Custom prompts
    st.subheader("Custom prompts (optional)")
    default_system_prompt = (
        "You are a senior media‑monitoring analyst. "
        "Your job is to summarise relevant industry news for an executive in the sector “{client_industry}”. "
        "Provide a one‑paragraph summary of the most important news. "
        "Exclude news specifically about the company “{client_company}”. "
        "Follow the rules strictly:\n"
        "• Work only with the information provided—no outside facts.\n"
        "• Cite your sources (e.g. ‘De Telegraaf schrijft …’).\n"
        "• Use the title and size of the news outlet to determine relevance.\n"
        "• Output only the summary and answer in {lang}.\n"
        "• Be concise; include only strictly necessary information."
    )

    default_user_prompt = (
        "RELEVANT INDUSTRY: {client_industry}\n"
        "Answer in {lang}\n"
        "Articles (Python list of titles): {titles}\n"
    )

    system_prompt = st.text_area("System prompt", default_system_prompt, height=180)
    user_prompt = st.text_area("User prompt", default_user_prompt, height=120)

    if st.button("Generate summaries"):
        st.session_state["run"] = True

# -----------------------------------------------------------------------------
# First‑run guard
# -----------------------------------------------------------------------------
if "run" not in st.session_state:
    st.info("Adjust parameters in the sidebar, then click **Generate summaries**.")
    st.stop()

# -----------------------------------------------------------------------------
# Parse model selection
# -----------------------------------------------------------------------------
opnai_models = []
run_gemini = False
chosen_gemini_model = None
run_perplexity_r1 = False
run_perplexity_sonar = False

for label in selected_labels:
    kind, name = model_options[label]
    if kind == "openai":
        opnai_models.append(name)
    elif kind == "gemini":
        run_gemini = True
        chosen_gemini_model = name
    elif kind == "perplexity_r1":
        run_perplexity_r1 = True
    elif kind == "perplexity_sonar":
        run_perplexity_sonar = True

# Fall‑back if user deselected every Gemini label
if not run_gemini:
    chosen_gemini_model = None

# -----------------------------------------------------------------------------
# Collect summaries
# -----------------------------------------------------------------------------
from scrapeGoogleNews import scrape_google_news  # local helper
import openai, requests, re
from google import genai
from google.genai.types import GenerateContentConfig

def _mk_openai(model, company, industry, query, lang, country, sys_p, user_p):
    articles = scrape_google_news(query, lang, country)
    titles = [a["title"] for a in articles]
    client = openai.OpenAI(api_key=st.secrets["openai_key"])
    msgs = [
        {
            "role": "system",
            "content": sys_p.format(
                client_company=company, client_industry=industry, lang=lang
            ),
        },
        {
            "role": "user",
            "content": user_p.format(
                client_company=company,
                client_industry=industry,
                lang=lang,
                titles=titles,
            ),
        },
    ]
    res = client.chat.completions.create(model=model, messages=msgs)
    return res.choices[0].message.content


def _mk_gemini(model, company, industry, query, lang, country, sys_p, user_p):
    articles = scrape_google_news(query, lang, country)
    titles = [a["title"] for a in articles]
    client = genai.Client(api_key='AIzaSyBVr_np1tN0jDvwJ6WQeVXYA6hzSqwTiOU')
    chat = client.chats.create(
        model=model,
        config=GenerateContentConfig(system_instruction=sys_p.format(
            client_company=company, client_industry=industry, lang=lang
        )),
    )
    prompt = user_p.format(
        client_company=company, client_industry=industry, lang=lang, titles=titles
    )
    resp = chat.send_message(prompt)
    return resp.text


def _mk_r1_1776(company, industry, query, lang, country, sys_p, user_p):
    import json

    API_KEY = "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"
    articles = scrape_google_news(query, lang, country)
    titles = [a["title"] for a in articles]
    payload = {
        "model": "r1-1776",
        "messages": [
            {"role": "system", "content": sys_p.format(
                client_company=company, client_industry=industry, lang=lang
            )},
            {"role": "user", "content": user_p.format(
                client_company=company, client_industry=industry, lang=lang, titles=titles
            )},
        ],
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    res = requests.post(
        "https://api.perplexity.ai/chat/completions", json=payload, headers=headers
    )
    res.raise_for_status()
    content = res.json()["choices"][0]["message"]["content"]
    return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)


# ---- collect ----
progress = st.progress(0.0, text="Collecting summaries…")

tasks = (
    len(opnai_models)
    + (1 if run_gemini else 0)
    + int(run_perplexity_r1)
    + int(run_perplexity_sonar)
)
if tasks == 0:
    st.error("Select at least one model.")
    st.stop()

done = 0
summaries = {}

for m in opnai_models:
    summaries[f"OpenAI ({m})"] = _mk_openai(
        m,
        client_company,
        client_industry,
        search_query,
        lang,
        country,
        system_prompt,
        user_prompt,
    )
    done += 1
    progress.progress(done / tasks, text=f"Collected {done}/{tasks}")

if run_gemini and chosen_gemini_model:
    summaries[f"Gemini ({chosen_gemini_model})"] = _mk_gemini(
        chosen_gemini_model,
        client_company,
        client_industry,
        search_query,
        lang,
        country,
        system_prompt,
        user_prompt,
    )
    done += 1
    progress.progress(done / tasks, text=f"Collected {done}/{tasks}")

if run_perplexity_r1:
    summaries["Perplexity (r1‑1776)"] = _mk_r1_1776(
        client_company,
        client_industry,
        search_query,
        lang,
        country,
        system_prompt,
        user_prompt,
    )
    done += 1
    progress.progress(done / tasks, text=f"Collected {done}/{tasks}")

if run_perplexity_sonar:
    summaries["Perplexity (sonar-pro)"] = get_industry_summary_perplexity(
        client_company,
        client_industry,
        search_query,
        lang,
    )
    done += 1
    progress.progress(done / tasks, text=f"Collected {done}/{tasks}")

progress.empty()

# -----------------------------------------------------------------------------
# Display & download
# -----------------------------------------------------------------------------
st.subheader("Overview")

date_str = os.environ.get("RUN_DATE")
if not date_str:
    import datetime as _dt
    date_str = _dt.date.today().isoformat()

body_lines = [f"# Sector News Overview ({date_str})", ""]
for src, txt in summaries.items():
    st.markdown(f"### {src}")
    st.markdown(txt)
    body_lines.append(f"---\n**{src}**\n{txt}\n")

md = "\n".join(body_lines)

st.download_button("Download as Markdown", md, file_name="sector_overview.md")

st.write("---")
st.caption("Powered by OpenAI, Gemini & Perplexity. Custom prompts supported.")
