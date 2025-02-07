import requests
import re
import urllib.parse
from bs4 import BeautifulSoup

print("All libraries are successfully imported!")

class Scanner:

    def __init__(self, url, ignore_links):
        self.session = requests.Session()
        self.target_url = url
        self.target_links = []
        self.links_to_ignore = ignore_links

    def extract_links_from(self, url):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # Raises an error for bad responses (4xx, 5xx)
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return []

        # Extract all href links (single and double quotes)
        links = re.findall(r'href=[\'"]?([^\'" >]+)', response.text)

        # Convert relative URLs to absolute URLs
        absolute_links = []
        for link in links:
            # Ignore JavaScript and empty links
            if link.startswith("javascript:") or link == "#":
                continue
            absolute_link = urllib.parse.urljoin(url, link)
            absolute_links.append(absolute_link)

        return absolute_links

    def crawl(self, url=None, depth=0, max_depth=3):
        if url is None:
            url = self.target_url

        if depth > max_depth:
            return  # Stop recursion if max depth is reached

        try:
            href_links = self.extract_links_from(url)
        except Exception as e:
            print(f"Skipping {url} due to error: {e}")
            return

        for link in href_links:
            link = urllib.parse.urljoin(url, link)

            if "#" in link:
                link = link.split("#")[0]

            # Ensure we only crawl links from the same domain
            if urllib.parse.urlparse(link).netloc == urllib.parse.urlparse(self.target_url).netloc:
                if link not in self.target_links and link not in self.links_to_ignore:
                    self.target_links.append(link)
                    print(f"Found: {link}")
                    self.crawl(link, depth + 1, max_depth)

    def extract_forms(self, url):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status() # Handles HTTP errors (e.g., 404, 500)
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return[]
        
        parsed_html = BeautifulSoup(response.text, "html.parser") # Use text instead of content
        return parsed_html.find_all("form") # `find_all` is preferred over `findAll`

        extracted_forms = []  # Ensure this is reachable

    for form in forms:
        form_details = {
            "action": form.get("action"),  
            "method": form.get("method", "get").lower(),
            "inputs": []
        }

        for input_tag in form.find_all("input"):  
            input_details = {
                "name": input_tag.get("name"),
                "type": input_tag.get("type", "text"),  # Default type is text
                "value": input_tag.get("value", "")
            }
            form_details["inputs"].append(input_details)
        
        extracted_forms.append(form_details)

    return extracted_forms  # Ensure this is reachable

