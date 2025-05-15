import requests
from bs4 import BeautifulSoup
import sys
import argparse
import subprocess
import os

# Define the maximum length for summaries to use in comparison
MAX_SUMMARY_LENGTH = 50

def scrape_with_cookies(url, cookies):
    """
    Scrapes a webpage for titles, truncating them, using provided cookies.

    Args:
        url: The URL of the webpage to scrape.
        cookies: A dictionary of cookies to use for the session.

    Returns:
        A list of truncated titles found, or None if an error occurred.
    """
    titles = []
    with requests.Session() as session:
        # Add the cookies to the session
        session.cookies.update(cookies)

        try:
            print(f"Attempting to scrape {url} with provided cookies...")
            response = session.get(url)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

            if response.status_code == 200:
                 print("Request successful. Parsing content.")
            else:
                 print(f"Request returned status code {response.status_code}. Cookies might be invalid or insufficient.", file=sys.stderr)
                 if len(response.text) < 1000: # Print partial response for debugging
                     print("Response content (partial):", response.text[:500] + '...' if len(response.text) > 500 else response.text, file=sys.stderr)
                 return None

            soup = BeautifulSoup(response.content, 'html.parser')
            td_tags = soup.find_all('td', class_='nav gerrit-subject')

            for td in td_tags:
                a_tag = td.find('a')
                if a_tag:
                    # Get text, strip whitespace, and truncate
                    full_title = a_tag.get_text(strip=True)
                    truncated_title = full_title[:MAX_SUMMARY_LENGTH]
                    titles.append(truncated_title)

            return titles

        except requests.exceptions.RequestException as e:
            print(f"Error fetching the URL: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"An error occurred during parsing: {e}", file=sys.stderr)
            return None

def save_matching_commits_to_file(matching_commits, filename="matching_commits.txt"):
    """
    Saves a list of (hash, summary) tuples to a text file, formatted as 'hash summary'.
    Note: The summary saved here is the (potentially truncated) one used for matching.
    """
    if not matching_commits:
        print(f"No matching commits found. {filename} will not be created.")
        return

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for commit_hash, summary in matching_commits:
                # The summary saved here is the truncated one used in comparison
                f.write(f"{commit_hash} {summary}\n")
        print(f"Matching commits successfully saved to {filename}")
    except IOError as e:
        print(f"Error writing to file {filename}: {e}", file=sys.stderr)


def get_commits_on_branch(repo_path, branch_name):
    """
    Gets commit hashes and truncated summaries for a branch in a git repo.
    Returns a list of (hash, truncated_summary) tuples, ordered by commit history.
    """
    commits = []
    if not os.path.isdir(repo_path):
        print(f"Error: Repository path '{repo_path}' is not a valid directory.", file=sys.stderr)
        return None

    command = ["git", "-C", repo_path, "rev-parse", "--show-toplevel"]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error: Directory '{repo_path}' does not appear to be a git repository.", file=sys.stderr)
        return None

    try:
        # Use git log to get commits in reverse chronological order (%H full hash, %s subject)
        command = ["git", "-C", repo_path, "log", "--pretty=format:%H %s", branch_name]
        print(f"Running git command: {' '.join(command)}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

        output_lines = result.stdout.strip().split('\n')
        for line in output_lines:
            if line:
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    commit_hash, full_summary = parts
                    # Truncate the commit summary
                    truncated_summary = full_summary[:MAX_SUMMARY_LENGTH]
                    commits.append((commit_hash, truncated_summary))
                else:
                    print(f"Warning: Skipping git log line with unexpected format: '{line}'", file=sys.stderr)

        return commits

    except FileNotFoundError:
        print(f"Error: 'git' command not found. Is Git installed and in your system's PATH?", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}", file=sys.stderr)
        print(f"Git command stderr:\n{e.stderr.strip()}", file=sys.stderr)
        if f"unknown revision or path not in the working tree" in e.stderr or f"ambiguous argument" in e.stderr:
             print(f"Error: Branch '{branch_name}' not found or invalid in repository '{repo_path}'.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred while getting git commits: {e}", file=sys.stderr)
        return None


def filter_titles_by_commits(scraped_titles_set, commits):
    """
    Filters the list of commits to find those whose *truncated* summaries match
    the provided set of *truncated* scraped titles.

    Args:
        scraped_titles_set: A set of unique *truncated* titles scraped from the web.
        commits: A list of (hash, *truncated_summary*) tuples from git log, in repository order.

    Returns:
        A list of (matching_hash, matching_truncated_summary) tuples, preserving
        the order from the 'commits' list.
    """
    matching_commits = []
    # Iterate through commits in their repository order (newest first from git log default)
    for commit_hash, truncated_summary in commits:
        # Check if the truncated commit summary exists in the set of truncated scraped titles
        if truncated_summary in scraped_titles_set:
            matching_commits.append((commit_hash, truncated_summary))
    return matching_commits


if __name__ == "__main__":
    # --- Set up argument parsing ---
    parser = argparse.ArgumentParser(
        description=f"Scrape Gerrit subject titles (truncated to {MAX_SUMMARY_LENGTH} chars) and match them against Git commits (truncated to {MAX_SUMMARY_LENGTH} chars) on a specific branch.",
        epilog="To get the JSESSIONID and atlassian.xsrf.token cookies from a"
        "chrome browser, open `Developer Tools` (<F12>), go to the "
        "`Application` tab, and open `Cookies` in the treeview on the left. "
        "`JSESSIONID` and `atlassian.xsrf.token` cookies should be shown on "
        "the right. Copy the values and provide them to this script.",
    )

    parser.add_argument(
        'jsessionid',
        help='The JSESSIONID cookie value required for Qt bug report authentication.',
        type=str
    )
    parser.add_argument(
        'atlassian_token',
        help='The atlassian.xsrf.token cookie value required for Qt bug report authentication.',
        type=str
    )
    parser.add_argument(
        'repo_path',
        help='The path to the local Git repository (e.g., /home/user/qt/qtbase).',
        type=str
    )
    parser.add_argument(
        'branch_name',
        help='The name of the Git branch to check (e.g., "dev", "6.6", "master").',
        type=str
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # --- Scrape titles from the webpage ---
    SCRAPE_URL = "https://bugreports.qt.io/browse/QTBUG-115777"
    YOUR_COOKIES = {
        'JSESSIONID': args.jsessionid,
        'atlassian.xsrf.token': args.atlassian_token,
    }
    print(f"Using JSESSIONID: {args.jsessionid[:5]}... (showing first 5 chars)")
    print(f"Using atlassian.xsrf.token: {args.atlassian_token[:5]}... (showing first 5 chars)")

    # scraped_titles list will now contain truncated titles
    scraped_titles = scrape_with_cookies(SCRAPE_URL, YOUR_COOKIES)

    if not scraped_titles:
        print("Failed to scrape titles from the webpage. Exiting.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(scraped_titles)} titles from webpage (truncated to {MAX_SUMMARY_LENGTH} chars).")

    # --- Process scraped titles (Sort and Make Unique) ---
    # Now sorting and unique-ing truncated titles
    sorted_scraped_titles = sorted(scraped_titles)
    unique_scraped_titles_set = set(sorted_scraped_titles) # Convert to set for efficient lookup

    print(f"Processed to {len(unique_scraped_titles_set)} unique sorted truncated titles for matching.")


    # --- Get commits from the local Git repository ---
    # repo_commits list will now contain (hash, truncated_summary) tuples
    repo_commits = get_commits_on_branch(args.repo_path, args.branch_name)

    if not repo_commits:
        print("Failed to get commits from the repository. Exiting.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(repo_commits)} commits on branch '{args.branch_name}' (summaries truncated to {MAX_SUMMARY_LENGTH} chars).")


    # --- Filter titles against commits ---
    # This compares the truncated summaries
    matching_commits = filter_titles_by_commits(unique_scraped_titles_set, repo_commits)

    # --- Save matching commits to a file ---
    # Saves the full hash and the truncated summary used for matching
    save_matching_commits_to_file(matching_commits)

    if matching_commits:
        print(f"Found and saved {len(matching_commits)} matching commits (hash and truncated summary) in repository order.")
    else:
        print("No matching commits found among the scraped titles and the history of the specified branch.")
