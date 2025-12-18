#!/usr/bin/env python3
"""
Araz Market Web Scraper
Extracts branch locations and details from arazmarket.az
"""

import csv
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import os


def scrape_araz_locations(url: str = "https://arazmarket.az/az/stores") -> List[Dict[str, str]]:
    """
    Scrape Araz market branch locations

    Args:
        url: URL of the Araz stores page

    Returns:
        List of dictionaries containing branch information
    """
    print(f"Fetching data from {url}...")

    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        response.encoding = 'utf-8'
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    branches = []

    # Find all store containers - try different selectors
    store_divs = soup.find_all('div', class_='page_list__v5vEU')

    # If not found with class, try finding by structure
    if not store_divs:
        # Try finding accordion items directly
        store_divs = soup.find_all('div', class_='accardion_accardionItem__Fyf_W')

    print(f"Found {len(store_divs)} branches")

    # Debug: print a sample of the HTML structure
    if len(store_divs) == 0:
        print("\nDebug: Could not find store divs. Checking page structure...")
        # Check if page has any divs with 'list' in class name
        all_divs = soup.find_all('div', class_=lambda x: x and 'list' in x.lower() if isinstance(x, str) else False)
        print(f"Found {len(all_divs)} divs with 'list' in class name")

        # Check if we got a valid HTML response
        if len(response.text) < 1000:
            print(f"Warning: Response seems too short ({len(response.text)} chars)")
            print("Response preview:", response.text[:500])

    for store_div in store_divs:
        try:
            # Find the accordion item
            accordion = store_div.find('div', class_='accardion_accardionItem__Fyf_W')
            if not accordion:
                continue

            # Extract name from the title toggle
            title_toggle = accordion.find('div', class_='accardion_accardionTitleToggle___WyGP')
            name_span = title_toggle.find('span') if title_toggle else None
            name = name_span.text.strip() if name_span else "N/A"

            # Find the content section
            content = accordion.find('div', class_='accardion_accardionContent__Vlwtt')
            if not content:
                continue

            # Extract address (first <p> tag)
            address_p = content.find('p')
            address = address_p.text.strip() if address_p else ""

            # Extract phone and hours from the options div
            options_div = content.find('div', class_='page_list_option__Cq36k')
            phone = ""
            hours = ""

            if options_div:
                # Extract phone
                phone_link = options_div.find('a', href=lambda x: x and x.startswith('tel:'))
                if phone_link:
                    phone = phone_link.text.strip()

                # Extract hours
                time_small = options_div.find('small')
                if time_small:
                    hours = time_small.text.strip()

            branch_data = {
                'name': name,
                'address': address,
                'phone': phone,
                'hours': hours
            }

            branches.append(branch_data)
            print(f"Extracted: {name}")

        except Exception as e:
            print(f"Error parsing branch: {e}")
            continue

    return branches


def save_to_csv(branches: List[Dict[str, str]], output_file: str) -> None:
    """
    Save branch data to CSV file

    Args:
        branches: List of branch dictionaries
        output_file: Path to output CSV file
    """
    if not branches:
        print("No data to save")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)

    fieldnames = ['name', 'address', 'phone', 'hours']

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(branches)

        print(f"\nSuccessfully saved {len(branches)} branches to {output_file}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")


def main():
    """Main execution function"""
    print("=" * 60)
    print("Araz Market Branch Scraper")
    print("=" * 60)

    # Scrape data
    branches = scrape_araz_locations()

    if branches:
        # Save to CSV
        output_file = 'data/araz.csv'
        save_to_csv(branches, output_file)

        # Print summary
        print("\n" + "=" * 60)
        print("Summary:")
        print(f"Total branches: {len(branches)}")
        print("=" * 60)
    else:
        print("\nNo branches found or error occurred")


if __name__ == "__main__":
    main()
