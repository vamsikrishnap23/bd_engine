import streamlit as st
import requests
import pandas as pd
import json
import os
from datetime import datetime
from urllib.parse import quote
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client

os.environ["STREAMLIT_WATCHDOG_USE_POLLING"] = "true"
import json
from supabase import create_client, Client
from storage3.utils import StorageException

from supabase_utils import supa_list_folders, supa_download_json, supa_upload_json, supa_upload_file, supa_upload_json, supa_upload_csv, supa_load_json




SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def supa_read_json(bucket: str, path: str):
    try:
        res = supabase.storage.from_(bucket).download(path)
        return json.loads(res.decode("utf-8"))
    except StorageException as e:
        print(f"[supa_read_json] Failed to read {path}: {e}")
        return None
    except Exception as e:
        print(f"[supa_read_json] Unknown error: {e}")
        return None


def supa_write_json(bucket: str, path: str, data: dict):
    try:
        return supabase.storage.from_(bucket).upload(
            path,
            json.dumps(data, indent=2),
            {"content-type": "application/json"},
            upsert=True
        )
    except Exception as e:
        print(f"[supa_write_json] Failed to write {path}: {e}")
        return None


def supa_read_text(bucket: str, path: str):
    try:
        res = supabase.storage.from_(bucket).download(path)
        return res.decode("utf-8")
    except StorageException as e:
        print(f"[supa_read_text] Failed to read {path}: {e}")
        return None


def supa_write_text(bucket: str, path: str, text: str):
    try:
        return supabase.storage.from_(bucket).upload(
            path,
            text,
            {"content-type": "text/plain"},
            upsert=True
        )
    except Exception as e:
        print(f"[supa_write_text] Failed to write {path}: {e}")
        return None


def supa_list_folders(bucket: str, prefix: str = ""):
    try:
        response = supabase.storage.from_(bucket).list(path=prefix)
        if response is None:
            print(f"[supa_list_folders] Got None for prefix: {prefix}")
            return []
        
        print(f"[supa_list_folders] Response for '{prefix}':", response)

        # Treat items without a dot (.) as folders
        folders = [item['name'] for item in response if '.' not in item['name']]
        return folders

    except Exception as e:
        print(f"[supa_list_folders] Error: {e}")
        return []



st.set_page_config(page_title="BD Engine", layout="wide")

st.image("assets/tp_logo.svg")


# os.makedirs("leads", exist_ok=True)


def fetch_linkedin_posts(linkedin_url, lead_dir):
    try:
        AGENT_ID = os.getenv("AGENT_ID")
        AUTH_TOKEN = os.getenv("AUTH_TOKEN")
        if not AGENT_ID or not AUTH_TOKEN:
            raise ValueError("Missing AGENT_ID or AUTH_TOKEN in environment variables")

        endpoint = f"https://api.tryrelevance.com/latest/agents/{AGENT_ID}/query"

        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": {
                "linkedin_url": linkedin_url
            }
        }

        res = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        posts = res.json().get("posts", [])
        # Save to file
        with open(os.path.join(lead_dir, "linkedin_posts.json"), "w") as f:
            json.dump(posts, f, indent=2)
        return posts
    except Exception as e:
        print("Post fetch error:", e)
        return []


def render_persona(persona):
    def orange_header(text):
        return f"<h5 style='color:#f77e0b;margin-bottom:4px'>{text}</h5>"

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(orange_header("Persona Type"), unsafe_allow_html=True)
        st.write(persona.get("persona_type", "-"))

        st.markdown(orange_header("Communication Style"), unsafe_allow_html=True)
        st.write(persona.get("communication_style", "-"))

        st.markdown(orange_header("Tone Profile"), unsafe_allow_html=True)
        st.write(persona.get("tone_profile", "-"))

        st.markdown(orange_header("Writing Style"), unsafe_allow_html=True)
        st.write(persona.get("writing_style", "-"))

    with col2:
        st.markdown(orange_header("Key Interests"), unsafe_allow_html=True)
        st.write(", ".join(persona.get("key_interests", [])) or "-")

        st.markdown(orange_header("Decision Drivers"), unsafe_allow_html=True)
        st.write(", ".join(persona.get("decision_drivers", [])) or "-")

        st.markdown(orange_header("Objection Style"), unsafe_allow_html=True)
        st.write(persona.get("objection_style", "-"))

    if persona.get("example_phrases"):
        st.markdown(orange_header("Example Phrases"), unsafe_allow_html=True)
        for phrase in persona["example_phrases"]:
            st.markdown(f"- _{phrase}_")

    st.markdown("<hr style='margin-top:1rem; margin-bottom:1rem'>", unsafe_allow_html=True)
    st.markdown(orange_header("Summary"), unsafe_allow_html=True)
    st.markdown(f"> {persona.get('summary', '-')}")





tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Scrape Leads", "Persona Dashboard", "Talk To Leads"])


with tab1:
    st.subheader("Scraped Leads Dashboard")

    dates = sorted(supa_list_folders("leads"), reverse=True)

    if not dates:
        st.info("No scrapes found. Run a scrape from the second tab.")
    else:
        selected_date = st.selectbox("Select Scrape Date", dates)

        lead_dirs = sorted(supa_list_folders("leads", prefix=f"{selected_date}/"))

        search_term = st.text_input("Search (name, email, company, title)", "").strip().lower()

        if not lead_dirs:
            st.warning("No leads found in this folder.")
        else:
            matches = 0
            for lead_name in lead_dirs:
                lead_path = f"{selected_date}/{lead_name}/lead.json"
                persona_path = f"{selected_date}/{lead_name}/persona.json"

                lead = supa_download_json("leads", lead_path)
                persona = supa_download_json("leads", persona_path)

                if not lead:
                    continue

                emp = next((e for e in lead.get("employment_history", []) if e.get("current")), {})
                full_name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}"
                email = lead.get("email", "")
                company = emp.get("organization_name", "")
                title = emp.get("title", "")
                searchable = f"{full_name} {email} {company} {title}".lower()

                if search_term and search_term not in searchable:
                    continue

                matches += 1
                photo = lead.get("photo_url", "")

                with st.expander(f"{full_name} - {title} @ {company}"):
                    cols = st.columns([1, 3])
                    with cols[0]:
                        if photo:
                            st.image(photo, width=100)
                    with cols[1]:
                        st.markdown(f"**Email:** {email}")
                        st.markdown(f"**LinkedIn:** [{lead.get('linkedin_url', '')}]({lead.get('linkedin_url', '')})")
                        st.markdown(f"**Location:** {lead.get('city', '')}, {lead.get('state', '')}, {lead.get('country', '')}")
                        st.markdown(f"**Seniority:** {lead.get('seniority', '')}")
                        st.markdown(f"**Industry:** {lead.get('industry', '')}")
                        st.markdown(f"**Departments:** {', '.join(lead.get('departments', []))}")

                    if persona:
                        st.markdown("---")
                        st.markdown("**Persona:**")
                        render_persona(persona)
                    else:
                        if st.button(f"Build Persona for {full_name}", key=f"btn_{lead_name}"):
                            from dotenv import load_dotenv
                            from openai import OpenAI
                            load_dotenv()
                            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

                            linkedin_url = lead.get("linkedin_url", "")
                            posts = fetch_linkedin_posts(linkedin_url, f"{selected_date}/{lead_name}")
                            post_snippets = "\n".join(posts[:5]) if posts else "No public posts available."

                            org = lead.get("organization", {})
                            skills = ', '.join(lead.get("skills", [])[:10])
                            tags = ', '.join(lead.get("tags", [])[:10])
                            keywords = ', '.join(org.get("keywords", [])[:15])
                            bio = lead.get("summary", "") or lead.get("bio", "")

                            prompt = f"""
                                You are an advanced persona modeling system for B2B outreach.

                                Given the full professional and public-facing information of a lead, construct a complete **behavioral persona** that can be used to simulate realistic conversations and generate personalized communication.

                                --- Personal Info ---
                                Name: {full_name}
                                Title: {title}
                                Seniority: {lead.get("seniority", "")}
                                Department: {', '.join(lead.get("departments", []))}
                                Skills: {skills}
                                Tags: {tags}
                                Bio: {bio}
                                Location: {lead.get("city", "")}, {lead.get("state", "")}, {lead.get("country", "")}
                                LinkedIn: {linkedin_url}

                                --- Company Info ---
                                Company: {company}
                                Industry: {org.get("industry", "")}
                                Company Size: {org.get("estimated_num_employees", "")} employees
                                Company Keywords: {keywords}

                                --- Writing Samples from LinkedIn Posts ---
                                {post_snippets}

                                --- Output Format ---
                                {{
                                "persona_type": "...",
                                "communication_style": "...",
                                "tone_profile": "...",
                                "writing_style": "...",
                                "key_interests": [...],
                                "decision_drivers": [...],
                                "objection_style": "...",
                                "example_phrases": [...],
                                "summary": "..."
                                }}
                            """

                            try:
                                response = client.chat.completions.create(
                                    model="gpt-4",
                                    messages=[{"role": "user", "content": prompt}],
                                    temperature=0.7
                                )

                                content = response.choices[0].message.content
                                persona = json.loads(content)

                                # Save persona to Supabase
                                supa_upload_json("leads", persona_path, persona)

                                st.success("Persona generated and saved.")
                                render_persona(persona)

                            except Exception as e:
                                st.error(f"Persona build failed: {e}")

            if matches == 0:
                st.warning("No leads matched your search.")



# -----------------------------------------
# TAB 2: SCRAPER
# -----------------------------------------
with tab2:
    st.subheader("Scrape New Leads")

    def add_query_param(name, values, query_parts):
        for v in values:
            encoded = quote(v.strip())
            query_parts.append(f"{name}[]={encoded}")

    with st.form("lead_form"):
        locations = st.text_input("Locations (comma-separated)", "Mumbai, Bangalore")
        businesses = st.text_input("Business Types (comma-separated)", "D2C")
        job_titles = st.text_input("Job Titles (comma-separated)", "Founder, CMO")
        submit = st.form_submit_button("Scrape Leads")

    if submit:
        with st.spinner("Scraping leads..."):

            query = {
                "location": [x.strip() for x in locations.split(",")],
                "business": [x.strip() for x in businesses.split(",")],
                "job_title": [x.strip() for x in job_titles.split(",")]
            }

            base_url = "https://app.apollo.io/#/people"
            query_parts = []

            add_query_param("personLocations", query["location"], query_parts)
            add_query_param("qOrganizationKeywordTags", query["business"], query_parts)
            add_query_param("personTitles", query["job_title"], query_parts)
            query_parts += [
                "sortByField=recommendations_score",
                "sortAscending=false",
                "page=1"
            ]

            final_url = f"{base_url}?{'&'.join(query_parts)}"
            st.markdown(f"[Apollo Search URL]({final_url})")

            TOKEN_APIFY = os.getenv("APIFY_TOKEN")

            apify_url = f"https://api.apify.com/v2/acts/code_crafter~apollo-io-scraper/run-sync-get-dataset-items?token={TOKEN_APIFY}"

            payload = {
                "getPersonalEmails": True,
                "getWorkEmails": True,
                "totalRecords": 500,
                "url": final_url
            }

            response = requests.post(apify_url, json=payload)

            if response.ok:
                leads = response.json()

                # Create path prefix for today
                today = datetime.now().strftime("%Y-%m-%d")
                bucket = "leads"
                prefix = f"{today}"

                df_rows = []

                for lead in leads:
                    full_name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".replace("/", "-")
                    emp = next((e for e in lead.get("employment_history", []) if e.get("current")), {})
                    phone_list = [p.get("number", "") for p in lead.get("phone_numbers", [])]

                    lead_subpath = f"{prefix}/{full_name}"

                    # Upload lead.json
                    supa_upload_json(bucket, f"{lead_subpath}/lead.json", lead)

                    row = {
                        "Full Name": full_name,
                        "Title": emp.get("title", ""),
                        "Company": emp.get("organization_name", ""),
                        "Email": lead.get("email", ""),
                        "LinkedIn": lead.get("linkedin_url", ""),
                        "City": lead.get("city", ""),
                        "State": lead.get("state", ""),
                        "Country": lead.get("country", ""),
                        "Seniority": lead.get("seniority", ""),
                        "Department": ', '.join(lead.get("departments", [])),
                        "Industry": lead.get("industry", ""),
                        "Skills": ', '.join(lead.get("skills", [])),
                        "Tags": ', '.join(lead.get("tags", [])),
                        "Phone Numbers": ', '.join(phone_list)
                    }

                    df_rows.append(row)

                    # Upload meta.csv for each lead
                    meta_df = pd.DataFrame([row])
                    supa_upload_csv(bucket, f"{lead_subpath}/meta.csv", meta_df)

                # Upload combined CSV
                full_df = pd.DataFrame(df_rows)
                supa_upload_csv(bucket, f"{prefix}/combined.csv", full_df)

                st.success(f"Scrape complete. {len(leads)} leads uploaded to Supabase under leads/{today}/")

            else:
                st.error("Failed to fetch leads from Apify.")
                st.text(response.text)


# -----------------------------------------
# TAB 3: PERSONA DASHBOARD
# -----------------------------------------
with tab3:
    case_study_df = pd.read_csv("case_studies.csv")

    st.subheader("All Leads with Personas")

    bucket = "leads"
    all_entries = []

    for date_folder in sorted(supa_list_folders(bucket), reverse=True):
        for lead_folder in supa_list_folders(bucket, prefix=f"{date_folder}/"):
            lead_path = f"{date_folder}/{lead_folder}/lead.json"
            persona_path = f"{date_folder}/{lead_folder}/persona.json"

            lead = supa_load_json("leads", lead_path)
            persona = supa_load_json("leads", persona_path)

            if lead and persona:
                emp = next((e for e in lead.get("employment_history", []) if e.get("current")), {})
                full_name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}"
                company = emp.get("organization_name", "")
                title = emp.get("title", "")
                email = lead.get("email", "")
                photo_url = lead.get("photo_url") or ""
                linkedin_url = lead.get("linkedin_url")

                all_entries.append({
                    "name": full_name,
                    "title": title,
                    "company": company,
                    "email": email,
                    "photo_url": photo_url,
                    "linkedin_url": linkedin_url,
                    "persona": persona,
                    "date": date_folder
                })


    if not all_entries:
        st.info("No personas found yet.")
    else:
       for entry in all_entries:
            with st.expander(f"{entry['name']} - {entry['title']} @ {entry['company']}"):
                cols = st.columns([1, 4])

                # -- LEFT COLUMN: Profile Image --
                with cols[0]:
                    if entry.get("photo_url"):
                        st.image(entry["photo_url"], width=100)
                    else:
                        st.write("No image available")

                # -- RIGHT COLUMN: Lead Info --
                with cols[1]:
                    st.markdown(f"**Email:** `{entry['email']}`")
                    st.markdown(f"**Scraped On:** `{entry['date']}`")
                    st.markdown(f"**Email Status:**")
                    linkedin_url = entry.get("linkedin_url", "")
                    if linkedin_url:
                        st.markdown(f"**LinkedIn:** [{linkedin_url}]({linkedin_url})")
                    else:
                        st.markdown("**LinkedIn:** `Not available`")

                st.divider()

                # -- Render Persona --
                render_persona(entry['persona'])

                # -- Email Generation Section --
                email_status_path = f"{entry['date']}/{entry['name']}/email_status.json"
                email_status = supa_load_json(bucket, email_status_path) or {}


                current_status = email_status.get("status", "Not started")
                st.markdown(f"**Current Email Status:** `{current_status.capitalize()}`")

                # If cold_email already exists
                if "cold_email" in email_status:
                    st.markdown("**Cold Email:**")
                    st.text_area("Cold Email", value=email_status["cold_email"], height=200, key=f"show_email_{entry['name']}")
                    st.download_button(
                        "Download Email",
                        email_status["cold_email"],
                        file_name=f"{entry['name'].replace(' ', '_')}_cold_email.txt",
                        key=f"download_{entry['name']}"
                    )

                    # Show recommended deck if present
                    if "recommended_deck" in email_status:
                        st.markdown(f"**Recommended Deck:** `{email_status['recommended_deck']}`")
                        st.markdown(f"[View Deck]({email_status.get('deck_url', '')})")
                        st.caption(email_status.get("deck_summary", ""))

                else:
                    if st.button(f"Generate Cold Email for {entry['name']}", key=f"email_btn_{entry['name']}"):
                        try:
                            from openai import OpenAI
                            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

                            with open("case_studies.json", "r", encoding="utf-8") as f:
                                case_studies = json.load(f)

                                case_studies_str = json.dumps(case_studies, indent=2)



                                prompt = f"""
                                    You are a creative strategist and cold outreach expert working for Team Pumpkin, a high-performance digital marketing agency.

                                    Team Pumpkin helps brands like Tata AIG, Pizza Hut, Boat, Himalaya, Axis Bank, etc. through digital marketing, influencer marketing, SEO, PR, and full-funnel strategy.

                                    Your job is to write a cold email to the lead below and pick the **most relevant case study deck** from the provided list to include in your message. 

                                    Make sure the email:
                                    - Embeds the selected **deck link directly**
                                    - Reflects their **persona traits** in tone, language, and content
                                    - Feels human, light, and tailored — not robotic or stiff

                                    --- Lead Info ---
                                    Name: {entry['name']}
                                    Title: {entry['title']}
                                    Company: {entry['company']}
                    
                                    --- Persona Traits ---
                                    Persona Type: {persona.get("persona_type", "-")}
                                    Communication Style: {persona.get("communication_style", "-")}
                                    Tone Profile: {persona.get("tone_profile", "-")}
                                    Writing Style: {persona.get("writing_style", "-")}
                                    Key Interests: {', '.join(persona.get("key_interests", []))}
                                    Decision Drivers: {', '.join(persona.get("decision_drivers", []))}
                                    Objection Style: {persona.get("objection_style", "-")}
                                    Example Phrases: {', '.join(persona.get("example_phrases", []))}
                                    Summary: {persona.get("summary", "-")}

                                    --- Case Study Decks ---
                                    {case_studies_str}


                                    --- Requirements ---
                                    - Carefully select **ONE** deck that is **highly relevant** to the lead’s industry, product type, and persona
                                    - Do NOT pick decks unrelated to their business domain (e.g. don’t pick “retail” for a D2C food brand)
                                    - Match persona tone
                                    - Use the lead’s communication style and objections to guide how persuasive vs casual the email should be
                                    - Use key interests or decision drivers to **anchor your pitch**
                                    - Embed the selected **deck link** directly into the email
                                    - Keep the email **under 150 words**
                                    - Use a friendly, non-pushy closing CTA (e.g., “Want to see what we could cook up?”)

                                    Always base your choice on the **tags and summaries** provided for each deck. Use the one that most **closely aligns with the lead’s interests, tone, and product type.**




                                    --- Format ---
                        
                                    Deck Chosen: <deck_name>
                                    Subject: ...
                                    Body:
                                    <cold email body here>
                                    """



                                response = client.chat.completions.create(
                                    model="gpt-4-turbo",
                                    messages=[{"role": "user", "content": prompt}],
                                    temperature=0.7
                                )

                                full_reply = response.choices[0].message.content

                                # Try to extract deck name
                                lines = full_reply.strip().splitlines()
                                deck_line = next((line for line in lines if line.lower().startswith("deck chosen:")), "")
                                chosen_deck = deck_line.replace("Deck Chosen:", "").strip()

                                # Match from CSV to get URL and summary
                                matched_deck_row = case_study_df[case_study_df['deck_name'].str.strip().str.lower() == chosen_deck.lower()]
                                if not matched_deck_row.empty:
                                    deck_url = matched_deck_row.iloc[0]["deck_url"]
                                    deck_summary = matched_deck_row.iloc[0]["deck_summary"]
                                else:
                                    deck_url = "Not found"
                                    deck_summary = "Not found"

                                # Save JSON
                                email_status = {
                                    "status": "cold",
                                    "cold_email": full_reply,
                                    "recommended_deck": chosen_deck,
                                    "deck_url": deck_url,
                                    "deck_summary": deck_summary,
                                    "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }

                                # Save email_status.json to Supabase
                                email_status_path = f"{entry['date']}/{entry['name']}/email_status.json"
                                supa_upload_json(bucket, email_status_path, email_status)

                                # Save cold_email.txt to Supabase
                                cold_email_txt_path = f"{entry['date']}/{entry['name']}/cold_email.txt"
                                supa_upload_file(bucket, cold_email_txt_path, full_reply.encode("utf-8"), file_options={"content-type": "text/plain"})


                                # UI Feedback
                                st.success("Cold email generated and saved.")
                                st.text_area("Cold Email", value=full_reply, height=220, key=f"textarea_{entry['name']}")
                                st.download_button(
                                    "Download Email",
                                    full_reply,
                                    file_name=f"{entry['name'].replace(' ', '_')}_cold_email.txt",
                                    key=f"download_after_gen_{entry['name']}"
                                )
                                st.markdown(f"**Recommended Deck:** `{chosen_deck}`")

                        except Exception as e:
                            st.error(f"Email generation failed: {e}")



with tab4:
    st.header("Talk To Leads")

    bucket = "leads"
    all_entries = []

    for date_folder in sorted(supa_list_folders(bucket), reverse=True):
        for lead_folder in supa_list_folders(bucket, prefix=f"{date_folder}/"):
            lead_path = f"{date_folder}/{lead_folder}/lead.json"
            persona_path = f"{date_folder}/{lead_folder}/persona.json"

            lead = supa_load_json(bucket, lead_path)
            persona = supa_load_json(bucket, persona_path)

            if lead and persona:
                full_name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}"
                all_entries.append({
                    "name": full_name,
                    "date": date_folder,
                    "folder": lead_folder,
                    "lead": lead,
                    "persona": persona
                })

    if not all_entries:
        st.warning("No leads with personas found.")
        st.stop()

    selected_label = st.selectbox("Choose a lead to talk to:", [f"{e['name']} ({e['date']})" for e in all_entries])
    selected_entry = next(e for e in all_entries if f"{e['name']} ({e['date']})" == selected_label)

    # Supabase chat path
    chat_path = f"{selected_entry['date']}/{selected_entry['folder']}/chat.json"
    messages = supa_load_json(bucket, chat_path)

    if not messages:
        messages = [{
            "role": "system",
            "content": f"""You are now simulating {selected_entry['name']}, a real-world professional based on detailed persona insights below.

Only respond in the tone, style, and mindset of this person. Use their vocabulary, preferred sentence structure, and emotional tone.

--- Persona Snapshot ---
{json.dumps(selected_entry['persona'], indent=2)}

--- Behavior Guidelines ---
- Be authentic to this person’s communication style (e.g., concise, assertive, formal, friendly).
- Reflect their interests and priorities when responding (e.g., ROI, efficiency, market trends).
- If a question is irrelevant or off-topic, politely redirect or decline.
- Keep your responses natural, as if you're typing on LinkedIn or replying to a thoughtful DM — not like an AI bot.

Your job is to answer **as if you are this person**, staying completely in character.
"""
        }]

    st.markdown("### Conversation")
    for msg in messages[1:]:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        elif msg["role"] == "assistant":
            st.markdown(f"**{selected_entry['name']}:** {msg['content']}")

    user_input = st.text_input("Your message:", key="talk_input")

    if st.button("Send") and user_input.strip():
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        messages.append({"role": "user", "content": user_input.strip()})
        with st.spinner("Thinking..."):
            try:
                res = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=messages,
                    temperature=0.7
                )
                reply = res.choices[0].message.content
                messages.append({"role": "assistant", "content": reply})

                supa_upload_json(bucket, chat_path, messages)

                st.experimental_rerun()

            except Exception as e:
                st.error(f"Conversation failed: {e}")


# ---------- footer  ----------
st.markdown("---")  # visual separator

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown(
        """
        <div style="text-align: center;">
            <a href="https://altara.in" target="_blank">
                <img src="https://altara.in/assets/Favicon-CkpRsanc.png" width="80" style="box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-radius: 8px;">
            </a>
            <p style="margin-top: 6px; font-size: 13px; color: black;">Built by ALTARA</p>
        </div>
        """,
        unsafe_allow_html=True
    )
