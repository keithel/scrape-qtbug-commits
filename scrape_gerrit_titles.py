import requests
from bs4 import BeautifulSoup
import sys

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

    # >>> YOU NEED TO OBTAIN YOUR AUTHENTICATION COOKIES <<<
    # Manually log in to bugreports.qt.io in your browser, then use browser developer tools
    # to find the cookies associated with the site. You'll likely need cookies like
    # JSESSIONID, atlassian.xsrf.token, etc.
    YOUR_COOKIES = {
        # Replace with your actual cookie names and values
        'JSESSIONID': 'YOUR_JSESSIONID_VALUE',
        'atlassian.xsrf.token': 'YOUR_ATLASSIAN_TOKEN',
        # Add other relevant cookies found in your browser
    }

    # IMPORTANT: Replace cookie values with your actual values. Cookies expire!
    # This method requires updating the cookies periodically.
    if 'JSESSIONID' not in YOUR_COOKIES or YOUR_COOKIES['JSESSIONID'] == 'YOUR_JSESSIONID_VALUE':
         print("ERROR: Please replace cookie values in YOUR_COOKIES with your actual cookies.", file=sys.stderr)
         print("You will need to manually log in and inspect your browser's cookies.", file=sys.stderr)
         sys.exit(1)


    gerrit_titles = scrape_with_cookies(SCRAPE_URL, YOUR_COOKIES)

    if gerrit_titles:
        save_titles_to_file(gerrit_titles)
    else:
        print("No titles were scraped, potentially due to invalid/expired cookies or no matching elements found.")
