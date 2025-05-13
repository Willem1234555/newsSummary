from scrapeGoogleNews import scrape_google_news
import openai
from google import genai
from google.genai.types import GenerateContentConfig
from determineRelevance import translate
import requests
import re

client = openai.OpenAI(api_key='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')

def get_industry_summary_openai(model, client_company, client_industry, search_query, lang, country):
    list_of_articles = scrape_google_news(search_query, lang, country)

    completion = client.chat.completions.create(
        model=model,

        messages=[
            # ---------- SYSTEM: permanent rules ----------
            {
                "role": "system",
                "content": (
                    "You are a senior media‑monitoring analyst. "
                    "Your job is to summarize relevant industry news for an executive in the following industry: "
                    f"“{client_industry}”, and to return a summary of the most import news stories in one paragraph. "
                    "You will be supplied with a list of article titles and sources that were found using a broad search term. "
                    f" Please exclude news specifically about the company: {client_company}."
                    " Follow these rules strictly:\n"
                    "• Work only with the information in the article provided—no outside facts.\n"
                    "• Cite your sources, e.g.: 'De Telegraaf schrijft ...'.\n"
                    "• Use the title and size of the news outlet to determine what to include.\n"
                    "• Output only the summary, and answer in Dutch.\n"
                    "• Answer concisely, only include strictly necessary information."
                )
            },

            # ---------- USER: task‑specific input ----------
            {
                "role": "user",
                "content": (
                    f"RELEVANT INDUSTRY: {client_industry}\n"
                    f"Answer in Dutch\n"
                    f"Articles, in the format of a python list of the titles and sources:"
                    f"{[article['title'] for article in list_of_articles]}\n"
                )
            }
        ]
    )

    return completion.choices[0].message.content


def get_industry_summary_gemini(
    model: str,
    client_company: str,
    client_industry: str,
    search_query: str,
    lang: str,
    country: str
) -> str:
    list_of_articles = scrape_google_news(search_query, lang, country)

    client = genai.Client(
        api_key='AIzaSyBVr_np1tN0jDvwJ6WQeVXYA6hzSqwTiOU'
    )

    chat_session = client.chats.create(
        model=model,
        config=GenerateContentConfig(
            system_instruction=(
                "You are a senior media-monitoring analyst. "
                "Your job is to summarize relevant industry news for an executive in the following industry: "
                f"“{client_industry}”, and to return a summary of the most important news stories in one paragraph. "
                "You will be supplied with a list of article titles and sources that were found using a broad search term. "
                f"Please exclude news specifically about the company: {client_company}. "
                "Follow these rules strictly:\n"
                "• Work only with the information in the article provided—no outside facts.\n"
                "• Cite your sources, e.g.: 'De Telegraaf schrijft ...'.\n"
                "• Use the title and size of the news outlet to determine what to include.\n"
                "• Output *only* the summary, no pleasentries and answer in English.\n"
                "• Answer concisely, only include strictly necessary information."
            ),
            temperature=0.1,
        ),
    )

    user_prompt = (
        f"RELEVANT INDUSTRY: {client_industry}\n"
        "Answer in Dutch\n"
        "Articles, in the format of a python list of the titles and sources: "
        f"{[article['title'] for article in list_of_articles]}"
    )
    response = chat_session.send_message(user_prompt)

    return translate(response.text, 'nl')

def remove_thinking(text: str) -> str:
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

def get_industry_summary_r1_1776(client_company, client_industry, search_query, lang, country):
    list_of_articles = scrape_google_news(search_query, lang, country)

    API_KEY = "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"
    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "r1-1776",
        "messages": [
            # ---------- SYSTEM: permanent rules ----------
            {
                "role": "system",
                "content": (
                    "You are a senior media‑monitoring analyst. "
                    "Your job is to summarize relevant industry news for an executive in the following industry: "
                    f"“{client_industry}”, and to return a summary of the most import news stories in one paragraph. "
                    "You will be supplied with a list of article titles and sources that were found using a broad search term. "
                    f" Please exclude news specifically about the company: {client_company}."
                    " Follow these rules strictly:\n"
                    "• Work only with the information in the article provided—no outside facts.\n"
                    "• Cite your sources, e.g.: 'De Telegraaf schrijft ...'.\n"
                    "• Use the title and size of the news outlet to determine what to include.\n"
                    "• Output only the summary, and answer in Dutch.\n"
                    "• Answer concisely, only include strictly necessary information."
                )
            },

            # ---------- USER: task‑specific input ----------
            {
                "role": "user",
                "content": (
                    f"RELEVANT INDUSTRY: {client_industry}\n"
                    f"Answer in Dutch\n"
                    f"Articles, in the format of a python list of the titles and sources:"
                    f"{[article['title'] for article in list_of_articles]}\n"
                )
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    return remove_thinking(response.json()['choices'][0]['message']['content'])


def get_industry_summary_perplexity(
        client_company: str,
        client_industry: str,
        search_query: str,
        lang: str
) -> dict:
    """Fetches industry summary with exclusion filters - FIXED VERSION"""

    API_KEY = "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"
    BASE_URL = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": (
                    "U bent een senior mediamonitoringanalist."
                    "Uw taak is om relevant nieuws uit de sector samen te vatten voor een leidinggevende in de volgende sector: "
                    f"{client_industry}, en een samenvatting te geven van de belangrijkste nieuwsberichten in één alinea. "
                    f" Sluit nieuws uit dat specifiek over het volgende bedrijf gaat: {client_company}."
                    f" Bezoek i.i.g. Google news, Bing news en Yahoo news. "
                    f" Antwoord met zinnen als: 'De Telegraaf schrijft ...'."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Geef een één alinea lange samenvatting van het belangrijkste nieuws "
                    f"in de sector \"{client_industry}\", voor een executive. "
                    f"Sluit alle berichten uit die specifiek over \"{client_company}\" gaan. "
                    f"Antwoord in het {lang}. Zoek ook op de term: {search_query}"
                )
            }
        ],
        "temperature": 0.1,
        "search_recency_filter": "day",
        "presence_penalty": 1.0,
        "web_search_options": {
            "search_context_size": "medium",
            "user_location": {"country": "NL"}
        }
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        BASE_URL,
        json=payload,
        headers=headers,
        timeout=10
    )

    return response.json()['choices'][0]['message']['content']


if __name__ == "__main__":
    search_query = 'bank OR banken OR bankieren OR economie OR rente OR ABN-AMRO OR Rabobank'
    print(get_industry_summary_r1_1776('ING', 'Banking / Finance', search_query, 'nl-NL', 'nl'))