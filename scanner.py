import re
import urllib.parse

import requests
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
            if (
                urllib.parse.urlparse(link).netloc
                == urllib.parse.urlparse(self.target_url).netloc
            ):
                if link not in self.target_links and link not in self.links_to_ignore:
                    self.target_links.append(link)
                    print(f"Found: {link}")
                    self.crawl(link, depth + 1, max_depth)

    def extract_forms(self, url):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # Handles HTTP errors (e.g., 404, 500)
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return []

        parsed_html = BeautifulSoup(response.text, "html.parser")
        forms = parsed_html.find_all("form")  # store extracted forms

        extracted_forms = []  # Ensure this is reachable

        for form in forms:
            form_details = {
                "action": form.get("action"),
                "method": form.get("method", "get").lower(),
                "inputs": [],
            }

            for input_tag in form.find_all("input"):
                input_details = {
                    "name": input_tag.get("name"),
                    "type": input_tag.get("type", "text"),  # Default type is text
                    "value": input_tag.get("value", ""),
                }
                form_details["inputs"].append(input_details)

            extracted_forms.append(form_details)

        return extracted_forms  # Ensure this is reachable

    def submit_form(self, form, payload, url):
        target_url = urllib.parse.urljoin(url, form.get("action"))
        method = form.get("method", "get").lower()

        form_data = {}
        for input_tag in form.get("inputs", []):
            input_name = input_tag.get("name")
            if input_name:
                form_data[input_name] = payload  # Inject payload into all form fields

        try:
            if method == "post":
                return self.session.post(target_url, data=form_data, timeout=10)
            else:
                return self.session.get(target_url, params=form_data, timeout=10)
        except requests.RequestException as e:
            print(f"Error submitting form to {target_url}: {e}")
            return None

    def run_scanner(self):
        if not self.target_links:
            print("[-] No target links found. Have you run the crawler")
            return

        for link in self.target_links:
            forms = self.extract_forms(link)
            for form in forms:
                print(f"[+] Testing in {link}")
                is_vulnerable_to_xss = self.test_xss_in_form(form, link)

                if is_vulnerable_to_xss:
                    print("-" * 50)
                    print(f"[*****] XSS discovered in {link} in the following form")
                    print(form)
                    print("-" * 50)

                if "=" in link:  # Only test links with query parameters
                    print(f"[+] Testing {link}")
                    is_vulnerable_to_xss = self.test_xss_in_link(link)

                    if is_vulnerable_to_xss:
                        print("-" * 50)
                        print(f"[*****] Discovered XSS in {link}")
                        print(link)
                        print("-" * 50)

    def test_xss_in_link(self, url):
        xss_test_script = "<sCript>alert('test')</scriPt>"

        # Parse the URL and modify query parameters safely
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Inject the payload into all parameters
        modified_params = {key: xss_test_script for key in query_params}

        # Reconstruct the URL with the payload
        modified_query = urllib.parse.urlencode(modified_params, doseq=True)
        modified_url = urllib.parse.urlunparse(
            (
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                modified_query,
                parsed_url.fragment,
            )
        )

        # Send the request
        response = self.session.get(modified_url)

        # Check if the script appears in the response
        return xss_test_script in response.text

    def test_xss_in_form(self, form, url):
        xss_test_script = "<sCript>alert('test')</scriPt>"

        # Submit form with the XSS payload
        response = self.submit_form(form, xss_test_script, url)

        # Check if the script appears in the response
        return xss_test_script in response.text
