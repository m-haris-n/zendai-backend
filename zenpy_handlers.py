from zenpy import Zenpy
import dotenv
import os
import json
import requests
import urllib.parse

dotenv.load_dotenv()

SUBDOMAIN = os.environ.get("SUBDOMAIN")
TOKEN = os.environ.get("API_TOKEN")
EMAIL = os.environ.get("EMAIL")

zp_client = Zenpy(subdomain=SUBDOMAIN, email=EMAIL, token=TOKEN)


START_DATE = "2023-11-12T23:19:00Z"
END_DATE = "2023-11-12T23:34:03Z"

query = f"query=type:ticket created>{START_DATE} created<{END_DATE}"
anotherurl = f"https://{SUBDOMAIN}.zendesk.com/api/v2/tickets.json?created>{START_DATE}&created<{END_DATE}"
asdfURL = (
    f"https://{SUBDOMAIN}.zendesk.com/api/v2/incremental/tickets?start_time=1099832100"
)


def get_search_url(subdomain, query=""):
    return f"https://{subdomain}.zendesk.com/api/v2/requests/search.json?{query}"


def get_all_tickets(token, subdomain):
    srchurl = get_search_url(subdomain=subdomain)
    response = requests.get(
        url=srchurl,
        headers={"Authorization": f"Basic {token}"},
    )
    resjson = response.json()
    tickets = resjson["requests"]

    cleanedData = []
    for ticket in tickets:
        cleanedData.append(
            {
                "id": ticket["id"],
                "assignee_id": ticket["assignee_id"],
                "subject": ticket["subject"],
                "description": ticket["description"],
                "created_ati": ticket["created_at"],
                "type": ticket["url"],
                "status": ticket["status"],
                "url": ticket["url"],
                "via": ticket["via"],
            }
        )
    return cleanedData


def get_ticket_by_id():
    return


def get_ticket_in_time_range():
    return


def get_ticket_by_agent():
    return
