import requests
from bs4 import BeautifulSoup
import sys
import argparse # Import the argparse module

# (Keep the scrape_with_cookies and save_titles_to_file functions as they were)
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

            # Optional: Check if the response content indicates a successful login
            # This is site-specific, but you could look for a known element
            # that only appears when logged in. For now, we rely on status_code.
            if response.status_code == 200:
                 print("Request successful. Parsing content.")
            else:
                 print(f"Request returned status code {response.status_code}. Cookies might be invalid or insufficient.", file=sys.stderr)
                 return None


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
    # --- Set up argument parsing ---
    parser = argparse.ArgumentParser(
        description="Scrape Gerrit subject titles from a Qt bug report page "
        "using JSESSIONID and atlassian.xsrf.token cookies.",
        epilog="To get the JSESSIONID and atlassian.xsrf.token cookies from a"
        "chrome browser, open `Developer Tools` (<F12>), go to the "
        "`Application` tab, and open `Cookies` in the treeview on the left. "
        "`JSESSIONID` and `atlassian.xsrf.token` cookies should be shown on "
        "the right. Copy the values and provide them to this script.",
    )
    parser.add_argument(
        'jsessionid',
        help='The JSESSIONID cookie value required for authentication.',
        type=str
    )
    parser.add_argument(
        'atlassian_token',
        help='The atlassian.xsrf.token cookie value required for authentication.',
        type=str
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # --- Use the provided cookies ---
    SCRAPE_URL = "https://bugreports.qt.io/browse/QTBUG-115777"

    # Construct the cookies dictionary using the provided arguments
    YOUR_COOKIES = {
        'JSESSIONID': args.jsessionid,
        'atlassian.xsrf.token': args.atlassian_token, # Include the atlassian token
    }

    print(f"Using JSESSIONID: {args.jsessionid[:5]}... (showing first 5 chars)")
    print(f"Using atlassian.xsrf.token: {args.atlassian_token[:5]}... (showing first 5 chars)")


    gerrit_titles = scrape_with_cookies(SCRAPE_URL, YOUR_COOKIES)

    if gerrit_titles:
        print(f"Found {len(gerrit_titles)} titles.")

        # --- Process the titles: Sort and Make Unique ---

        # 1. Sort the list alphabetically
        sorted_titles = sorted(gerrit_titles)
        print(f"Titles sorted.")

        # 2. Make the list unique while maintaining sorted order
        unique_sorted_titles = list(dict.fromkeys(sorted_titles))
        print(f"Reduced to {len(unique_sorted_titles)} unique titles.")

        # --- Save the processed titles ---
        save_titles_to_file(unique_sorted_titles)
    else:
        print("No titles were scraped or an error occurred. Please check your cookies.")
