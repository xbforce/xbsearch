#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
xbsearch.py

A command-line tool to search a list of words on DuckDuckGo, extract domains from
the search results, and save the unique domains to an output file.
"""

import argparse
import sys
import time
from urllib.parse import urlparse
from datetime import datetime
import re

# This tool now uses the 'ddgs' library, which is the new name for
# 'duckduckgo_search'. It is generally more permissive for automated searching
# than direct Google scraping.
# You can install it with: `pip install ddgs`
try:
    from ddgs import DDGS
except ImportError:
    print("[ERROR] The 'ddgs' library is not installed. Please install it with:")
    print("        pip install ddgs")
    sys.exit(1)

def perform_duckduckgo_search(query, num_results=30, verbose=False):
    """
    Performs a real DuckDuckGo search for a given query.

    Args:
        query (str): The search query.
        num_results (int): The maximum number of search results to retrieve.
                           This is calculated by pages * 10.
        verbose (bool): If True, prints detailed search information.

    Returns:
        list: A list of real URLs from the search results.
    """
    all_urls = set()
    if verbose:
        print(f"    [INFO] Searching DuckDuckGo for: '{query}'")
    try:
        # Use DDGS().text() to get text-based search results.
        # The 'query' parameter is now explicitly used, as indicated by the error.
        with DDGS() as ddgs:
            ddgs_results = ddgs.text(query=query, max_results=num_results)
            for result in ddgs_results:
                if 'href' in result:
                    all_urls.add(result['href'])
    except Exception as e:
        # A newline is added here to ensure the error message doesn't
        # overwrite the live status update.
        print(f"\n[ERROR] A search error occurred: {e}", file=sys.stderr)
        return []
        
    return list(all_urls)

def main():
    """
    Main function to run the xbsearch.py tool.
    """
    parser = argparse.ArgumentParser(
        description="Search a list of words on DuckDuckGo and gather unique domains.",
        epilog="""
        Examples:
          python3 xbsearch.py -f words.txt
          python3 xbsearch.py -f words.txt -p 10
          python3 xbsearch.py -f words.txt -o mydomains.txt -d "site:*.net"
        """
    )

    parser.add_argument('-f', '--file',
                        type=str,
                        help="Path to a file containing a list of words (one per line).",
                        required=True)

    parser.add_argument('-o', '--output',
                        type=str,
                        default=None,
                        help="Path to the output file to save unique domains. Defaults to xb_DDMMYYHHMM.txt if not specified.")
                        
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help="Show detailed search information for each word (off by default).")
    
    parser.add_argument('-d', '--dork',
                        type=str,
                        default=None,
                        help="A DuckDuckGo dork to append to each search query (e.g., 'site:*.com').")

    parser.add_argument('-p', '--pages',
                        type=int,
                        default=3,
                        help="The number of search result pages to retrieve (default: 3, each page has ~10 results).")

    args = parser.parse_args()

    input_file = args.file
    output_file = args.output
    verbose = args.verbose
    dork = args.dork
    pages = args.pages

    # If no output file is specified, create a default one
    if not output_file:
        timestamp = datetime.now().strftime("%d%m%y%H%M")
        output_file = f"xbsea_{timestamp}.txt"
        print(f"[INFO] No output file specified. Using default: '{output_file}'")


    # Calculate max_results based on pages, assuming ~10 results per page.
    num_results = pages * 10

    # Read words from the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[ERROR] Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    if not words:
        print(f"[ERROR] Input file is empty: {input_file}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Processing {len(words)} words from '{input_file}'...")

    # Extract the TLD from the dork for post-filtering
    dork_tld_filter = None
    if dork:
        # Simple regex to extract the domain/TLD part from a "site:*.tld" dork
        match = re.search(r'site:\*\.(?P<tld>[a-zA-Z0-9\-\.]+)', dork)
        if match:
            dork_tld_filter = "." + match.group('tld').lower()
            if verbose:
                print(f"[INFO] Filtering results to only include domains ending in '{dork_tld_filter}'")

    found_domains = set()
    words_processed = 0

    # Process each word and perform the search
    for word in words:
        words_processed += 1
        
        # Live status update
        status_message = (
            f"[STATUS] Progress: {words_processed}/{len(words)} words processed. "
            f"Domains collected: {len(found_domains):<5}"
        )
        sys.stdout.write('\r' + status_message)
        sys.stdout.flush()

        # Construct the query by combining the word and the optional dork
        search_query = f"{word} {dork}" if dork else word

        # Perform the search and process results
        try:
            # Pass the calculated num_results to the search function
            search_results = perform_duckduckgo_search(search_query, num_results=num_results, verbose=verbose)
            for url in search_results:
                try:
                    # Use urlparse to get scheme and netloc, then reconstruct with a trailing slash
                    parsed_url = urlparse(url)
                    if parsed_url.netloc:
                        # Perform post-filtering if a dork TLD was specified
                        if dork_tld_filter and not parsed_url.netloc.lower().endswith(dork_tld_filter):
                            continue # Skip this domain if it doesn't match the dork's TLD

                        # Reconstruct the URL with protocol and a trailing slash
                        full_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
                        found_domains.add(full_url)
                except ValueError as e:
                    if verbose:
                        print(f"\n[WARNING] Skipping malformed URL: {url} ({e})", file=sys.stderr)
        except Exception as e:
            if verbose:
                print(f"\n[ERROR] Failed to search for '{search_query}': {e}", file=sys.stderr)
            continue

    # Final status update
    sys.stdout.write('\r' + status_message + ' - DONE\n')

    # Write the unique domains to the output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for domain in sorted(list(found_domains)):
                f.write(f"{domain}\n")
        print(f"[SUCCESS] Successfully collected {len(found_domains)} unique domains to '{output_file}'.")
    except IOError as e:
        print(f"[ERROR] Failed to write to output file '{output_file}': {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
