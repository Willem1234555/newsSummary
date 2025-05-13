import openai
import pandas as pd
import json
from deep_translator import GoogleTranslator

client_company = 'ING'
client = openai.OpenAI(api_key='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')

def translate(text, target_lan = 'en'):
    return GoogleTranslator(source='auto', target=target_lan).translate(text)

def get_relevance(article: dict):
    if 'source_name' not in article:
        article['source_name'] = 'UNKNOWN'

    if 'published_date' not in article:
        article['published_date'] = 'UNKNOWN'

    completion = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        # ‑‑‑ force well‑formed JSON so downstream code never has to regex‑clean
        response_format={"type": "json_object"},

        messages=[
            # ---------- SYSTEM: permanent rules ----------
            {
                "role": "system",
                "content": (
                    "You are a senior media‑monitoring analyst. "
                    "Your job is to decide the importance of the given article to an executive at the Dutch company "
                    f"“{client_company}” (including all subsidiaries and brands) and to return a "
                    "short justification.  Follow these rules strictly:\n"
                    "• Work only with the information in the article provided—no outside facts.\n"
                    "• If the company is not substantively mentioned, the score must be ≤ 30.\n"
                    "• Sentiment is the overall tone toward the company (positive, neutral, negative).\n"
                    "• Output *valid JSON only* with the exact keys and types shown below—no extra text.\n"
                    "• JSON schema to return:\n"
                    "  {\n"
                    "    \"score\": integer   # 0–100 relevance strength\n"
                    "    \"sentiment\": \"positive\" | \"neutral\" | \"negative\",\n"
                    "    \"source_type\": string   # e.g. online, newspaper, trade press, blog\n"
                    "    \"rationale\": string     # ≤20 words, quote or paraphrase a key line\n"
                    "  }"
                )
            },

            # ---------- USER: task‑specific input ----------
            {
                "role": "user",
                "content": (
                    f"CLIENT COMPANY: {client_company}\n"
                    f"ARTICLE SOURCE: {article['source_name']}\n"
                    f"ARTICLE DATE: {article['published_date']}\n\n"
                    "ARTICLE TEXT:\n\"\"\"\n"
                    f"{translate(article['text'])}\n\"\"\"\n\n"
                    "TASK:\n"
                    "1. Rate how strongly this coverage affects the client on the 0–100 scale:\n"
                    "   • 0: no relevance\n"
                    "   • 50: mentions the client in passing or small operational impact\n"
                    "   • 100: critical strategic impact (e.g., legal ruling, takeover, scandal)\n"
                    "2. Identify overall sentiment toward the client.\n"
                    "3. Return JSON using the schema above—nothing else."
                )
            }
        ]
    )

    json_obj = completion.choices[0].message.content

    return json.loads(json_obj)

def list_of_json_to_xlsx(list_of_json: list):
    df = pd.DataFrame(list_of_json)

    columns_order = ['score', 'sentiment', 'source_type', 'rationale']
    df = df[columns_order]
    output_path = 'ING_relevance_scores.xlsx'
    df.to_excel(output_path, index=False)

def main():
    responses = []
    article_texts = pd.read_excel('scraped_nos_articles_scored.xlsx').get('Article Text')[50:52]

    for article_text in article_texts:
        article = {'text': article_text, 'source_name': 'NOS'}
        responses.append(get_relevance(article))

    list_of_json_to_xlsx(responses)

if __name__ == '__main__':
    main()