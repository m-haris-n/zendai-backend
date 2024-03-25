from zenpy import Zenpy
import dotenv
import os
import json
import requests
import urllib.parse

dotenv.load_dotenv()


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
