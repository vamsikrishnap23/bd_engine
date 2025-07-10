
                                    prompt = f"""
                                        You are an advanced persona modeling system for B2B outreach.

                                        Given the full professional and public-facing information of a lead, construct a complete **behavioral persona** that can be used to simulate realistic conversations and generate personalized communication.

                                        ---

                                        # Personal Info:
                                        Full Name: {full_name}
                                        Job Title: {title}
                                        Seniority: {lead.get("seniority", "")}
                                        Department: {', '.join(lead.get("departments", []))}
                                        Skills: {skills}
                                        Tags: {tags}
                                        Bio: {bio}
                                        Location: {lead.get("city", "")}, {lead.get("state", "")}, {lead.get("country", "")}
                                        LinkedIn: {linkedin_url}

                                        ---

                                        # Company Info:
                                        Company: {company}
                                        Industry: {org.get("industry", "")}
                                        Company Size: {org.get("estimated_num_employees", "")} employees
                                        Company Keywords: {keywords}

                                        ---

                                        # Recent LinkedIn Posts:
                                        {chr(10).join(posts[:15]) if posts else 'No public posts available.'}

                                        ---

                                        # Output Format (Respond ONLY in JSON):
                                        {{
                                        "persona_type": "e.g. visionary, detail-oriented, process-driven",
                                        "communication_style": "e.g. concise, storytelling, data-heavy, casual",
                                        "tone_profile": "e.g. assertive, humble, upbeat, skeptical",
                                        "writing_style": "e.g. short bullet points, long paragraphs, emoji-friendly, formal",
                                        "key_interests": ["product-led growth", "team building", "data analytics"],
                                        "decision_drivers": ["speed", "scalability", "ROI", "founder alignment"],
                                        "objection_style": "e.g. asks tough ROI questions, cautious about cost, slow to respond",
                                        "example_phrases": [
                                            "We’re bootstrapped, so efficiency matters.",
                                            "I care more about retention than reach.",
                                            "We’re not in a rush — we move with intent."
                                        ],
                                        "summary": "A data-focused growth leader who values clarity, control, and team strength."
                                        }}
                                        """