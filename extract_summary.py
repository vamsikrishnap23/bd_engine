import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load your OpenAI key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 1. Scrape Pages
urls = [
    "https://teampumpkin.com/",
    "https://teampumpkin.com/about-our-company",
    "https://teampumpkin.com/intro-deck/index"
]

def extract_text_from_url(url):
    try:
        res = requests.get(url, timeout=300)
        soup = BeautifulSoup(res.text, "html.parser")

        for tag in soup(["script", "style", "noscript", "nav", "footer"]):
            tag.decompose()

        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

combined_text = "\n\n".join(extract_text_from_url(url) for url in urls)

# 2. Build Prompt for GPT
prompt = f"""
You are an expert B2B strategist working on behalf of a digital marketing agency called **Team Pumpkin**.

You are given content scraped from their official website.

Your goal is to write a **5-point professional summary** that clearly outlines the agency's **marketing strengths**, so it can be used to:

- Generate cold emails to potential leads
- Match relevant case studies and decks
- Position Team Pumpkin competitively during outreach

Your output must include:

1. **What marketing services Team Pumpkin offers** (focus on performance, creative, media, etc.)
2. **What kinds of brands or industries they serve** (e.g., FMCG, D2C, fashion, tech, etc.)
3. **Unique value propositions or tone** (e.g., performance-driven, youth-focused, full-funnel, etc.)
4. **Any specific brand names, clients, or case studies** mentioned on their website (list as many as found)
5. **Their approach to marketing** (e.g., strategy, execution, analytics, storytelling, etc.)

Be concise and factual. Bullet points only. Skip general fluff or repeating their name unnecessarily.

---

"""


# 3. Ask GPT-4
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.5
)

summary = response.choices[0].message.content.strip()

# 4. Save to File (optional)
with open("team_pumpkin_summary.txt", "w", encoding="utf-8") as f:
    f.write(summary)

print("\n--- Team Pumpkin BD Summary ---\n")
print(summary)
