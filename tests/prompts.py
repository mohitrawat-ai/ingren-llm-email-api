import unittest
from langsmith.client import Client, convert_prompt_to_openai_format

promptObject =  {
                        "prospect_first_name": "Sarah",
                        "prospect_last_name": "Johnson",
                        "prospect_job_title": "VP of Sales",
                        "prospect_department": "Sales",
                        "prospect_tenure_months": 18,
                        "prospect_notable_achievement": "Exceeded Q1 targets by 27%",
                        "company_name": "TechNova Solutions",
                        "company_industry": "SaaS",
                        "company_employee_count": "250",
                        "company_annual_revenue": "$45M",
                        "company_funding_stage": "Series B",
                        "company_growth_signals": "30% YoY growth, hiring burst in sales",
                        "company_recent_news": "Launched new enterprise product line",
                        "company_technography": "Salesforce, Marketo, Outreach.io",
                        "company_description": "Cloud-based project management software",
                        "cta_ask": "15-min chat next Tuesday?",
                        "cta_calendar_link": "calendly.com/ingren/demo",
                        "email_tone": "professional",
                        "sender_name": "John Doe",
                        "seller_product_name": "Ingren.ai",
                        "seller_category": "AI‑powered outbound automation",
                        "seller_headline_benefit": "Turns 8 hrs of prospect research into 8 min",
                        "seller_unique_proof": "87% faster research → 22% more first‑call bookings",
                        "seller_marquee_case_studies": ""
                }


class MyTestCase(unittest.TestCase):
    def test_something(self):

        # langsmith client
        client = Client()

        # pull prompt and invoke to populate the variables
        prompt = client.pull_prompt("ingren_email_user", include_model=False)
        prompt_value = prompt.invoke({})

        openai_payload = convert_prompt_to_openai_format(prompt_value)
        print(openai_payload["messages"][0]["content"])
        assert openai_payload != ""        # add assertion here


if __name__ == '__main__':
    unittest.main()
