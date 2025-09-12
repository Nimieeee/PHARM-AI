import requests
from bs4 import BeautifulSoup
from config import HEADERS

class Website:
    def __init__(self, url: str):
        self.url = url
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")

        self.title = soup.title.string if soup.title else "No title found"

        # Remove unwanted elements
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()

        self.text = soup.body.get_text(separator="\n", strip=True)

    def __repr__(self):
        return f"Website(title={self.title!r}, url={self.url!r})"
