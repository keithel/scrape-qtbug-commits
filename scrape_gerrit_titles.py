import requests
from bs4 import BeautifulSoup
import sys

# (Keep the scrape_with_cookies and save_titles_to_file functions as they were in Method 2)
# ... copy the functions from the previous response ...

def scrape_with_cookies(url, cookies):
    """
    Scrapes a webpage using provided cookies to maintain a session.

    Args:
        url: The URL of the webpage to scrape.
        cookies: A dictionary of cookies to use for the session.

    Returns:
        A list of titles found, or None if an error occurred.
    """
    titles = []
    with requests.Session() as session:
        # Add the cookies to the session
        session.cookies.update(cookies)

        try:
            print(f"Attempting to scrape {url} with provided cookies...")
            response = session.get(url)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            print("Request successful. Parsing content.")

            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all <td> tags with the class "nav gerrit-subject"
            td_tags = soup.find_all('td', class_='nav gerrit-subject')

            # Extract the title from the <a> tag within each <td>
            for td in td_tags:
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
    SCRAPE_URL = "https://bugreports.qt.io/browse/QTBUG-115777"

    # >>> YOUR OBTAINED COOKIES HERE <<<
    # Replace with your actual cookie names and values
    YOUR_COOKIES = {
        'JSESSIONID': 'YOUR_JSESSIONID_VALUE', # Replace with your actual JSESSIONID
        'atlassian.token': 'YOUR_ATLASSIAN_TOKEN_VALUE', # Replace with your actual atlassian.token
        # Add other relevant cookies found in your browser
    }

    # Check if default cookie values are still present
    if 'JSESSIONID' not in YOUR_COOKIES or YOUR_COOKIES['JSESSIONID'] == 'YOUR_JSESSIONID_VALUE':
         print("ERROR: Please replace cookie values in YOUR_COOKIES with your actual cookies.", file=sys.stderr)
         print("You will need to manually log in and inspect your browser's cookies.", file=sys.stderr)
         sys.exit(1)

    gerrit_titles = scrape_with_cookies(SCRAPE_URL, YOUR_COOKIES)

    if gerrit_titles:
        print(f"Found {len(gerrit_titles)} titles.")

        # --- Process the titles: Sort and Make Unique ---

        # 1. Sort the list alphabetically
        # sorted() returns a new sorted list
        sorted_titles = sorted(gerrit_titles)
        print(f"Titles sorted.")

        # 2. Make the list unique while maintaining sorted order
        # An elegant way in modern Python (3.7+) is using dict.fromkeys
        # which preserves insertion order. Converting to a list gets the unique items.
        unique_sorted_titles = list(dict.fromkeys(sorted_titles))
        print(f"Reduced to {len(unique_sorted_titles)} unique titles.")

        # --- Save the processed titles ---
        save_titles_to_file(unique_sorted_titles)
    else:
        print("No titles were scraped or an error occurred.")
