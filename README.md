# pre_funnel

A backend-only Python Flask app for automated B2B lead discovery and enrichment. Input a few emails, company info, and a goal; get back enriched, ranked leads and custom outreach messages as JSON.

## Usage

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run the server:
   ```
   python app.py
   ```
3. Send a POST request to `http://localhost:5000/api/lead-discovery` with your input JSON.

## Features

* **Goal Interpretation:** Uses AI to understand your networking or sales objective and generate search strategies.
* **Multi-Channel Scouting:** Finds profiles using email lookup, LinkedIn, X/Twitter, and general internet research.
* **Profile Validation & Ranking:** Deduplicates and scores profiles for best fit to your goal.
* **Drafted Outreach Messages:** Generates personalized messages for each discovered lead.
* **Easy API:** Simple Flask API server—connect to any frontend or automation tool.

## How It Works

1. **POST** a JSON payload with your emails, company info, and networking goal.
2. The backend:

   * Interprets your goal
   * Scouts profiles from multiple sources
   * Validates and ranks results
   * Drafts outreach messages
3. **Receives** a JSON list of enriched leads with ready-to-send messages.

## Example Input

```json
{
  "emails": ["jane@example.com"],
  "company_info": "Acme AI",
  "goal": "Find Bay Area startup founders looking for voice agents",
  "target": 5
}
```

## Example Output

```json
{
  "profiles": [
    {
      "name": "Jane Doe",
      "email": "jane@example.com",
      "title": "Founder",
      "company": "Acme AI",
      "linkedin": "https://linkedin.com/in/janedoe",
      "x_handle": "@janedoeai",
      "public_links": [],
      "message": "Hi Jane Doe, I noticed you're at Acme AI. We're reaching out regarding Find Bay Area startup founders looking for voice agents. Let's connect! - Acme AI"
    },
    ...
  ]
}
```

## Roadmap

* Integrate real data APIs (People Data Labs, SaleLeads, Twitter API, Gemini LLM, etc.)
* Add authentication, logging, and error handling
* (Optional) Deploy to cloud or connect to a web frontend

---

**Pre-Funnel is your AI research assistant for smarter B2B outreach.**
Contributions and feedback welcome!

--- 