import requests
from bs4 import BeautifulSoup
import sys

def scrape_gerrit_titles(url):
    """
    Scrapes a webpage for titles within <td class="nav gerrit-subject"><a> tags.

    Args:
        url: The URL of the webpage to scrape.

    Returns:
        A list of titles found, or None if an error occurred.
    """
    titles = []
    try:
        # Fetch the webpage content
        response = requests.get(url)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        print(f"Finding all td tags in {str(url)}")
        print(f"content: {str(response.content)}")
        # Find all <td> tags with the class "nav gerrit-subject"
        td_tags = soup.find_all('td')#, class_='nav gerrit-subject')
        print(f"td_tags len: {len(td_tags)}")

        # Extract the title from the <a> tag within each <td>
        for td in td_tags:
            print(f"Found <td class=\"nav gerrit-subject\">")
            a_tag = td.find('a')
            if a_tag:
                titles.append(a_tag.get_text(strip=True))

        return titles

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An error occurred during parsing: {e}", file=sys.stderr)
        return None

def save_titles_to_file(titles, filename="titles.txt"):
    """
    Saves a list of titles to a text file, one title per line.

    Args:
        titles: A list of titles.
        filename: The name of the file to save the titles to.
    """
    if titles is None:
        return

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for title in titles:
                f.write(title + '\n')
        print(f"Titles successfully saved to {filename}")
    except IOError as e:
        print(f"Error writing to file {filename}: {e}", file=sys.stderr)

if __name__ == "__main__":
    url = "https://bugreports.qt.io/browse/QTBUG-115777"
    gerrit_titles = scrape_gerrit_titles(url)

    if gerrit_titles:
        save_titles_to_file(gerrit_titles)
    else:
        print("No titles were scraped due to an error or no matching elements found.")
