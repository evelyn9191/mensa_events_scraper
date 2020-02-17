import datetime
import re
from typing import List

import requests

from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from email_data import sender, receiver, openkeyword


def get_events() -> List[tuple]:
    today = datetime.datetime.today()
    next_month = today.month + 1 if today.month < 12 else 1
    relevant_year = today.year if next_month > 1 else today.year + 1
    url = f"http://www.mensa.cz/volny-cas/detail-akce?mesic={next_month}&rok={relevant_year}&s_month={next_month}"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 "
                             "Safari/537.36"}
    response = requests.get(url, headers=headers)
    html = response.text

    soup = BeautifulSoup(html, 'lxml')
    events = soup.find_all("td", class_="popis")

    relevant_events = get_relevant_events(events)

    return relevant_events


def get_relevant_events(events: list):

    filtered_events = []

    for event in events:
        title = event.contents[0].attrs["title"]
        wanted_event = _is_event_wanted(title)

        if not wanted_event:
            continue

        link = event.contents[0].attrs["href"]
        filtered_events.append((title, link))

    return filtered_events


def _is_event_wanted(title: str) -> bool:
    events_to_avoid = ["testování", "IQ testy", "Uzávěrka časopisu Mensa", "MotivP", "Mensy gymnázia", "intranet", "děti", "dětech"]

    for unwanted_event in events_to_avoid:
        if unwanted_event.lower() in title.lower():
            return False

    non_prague_event = re.search("MS (?!Praha)", title)
    if non_prague_event:
        return False

    return True


def create_email(events: List[tuple], fromaddr: str, toaddr: str, openkeyword: str):
    """Send email with article titles and their urls."""
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = toaddr
    msg['Subject'] = 'Nové akce Mensy'
    body = MIMEText(('\n\n'.join('{}\n{}'.format(title, url) for (title, url) in events)), 'plain')
    msg.attach(body)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.connect('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(fromaddr, openkeyword)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
    print("Email successfully sent!")


if __name__ == "__main__":
    events = get_events()
    create_email(events, sender, receiver, openkeyword)
