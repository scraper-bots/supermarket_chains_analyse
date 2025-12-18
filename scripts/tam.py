#!/usr/bin/env python3
"""
TAM Store Web Scraper
Extracts branch locations and details from tamstore.az API
"""

import csv
import requests
from typing import List, Dict
import os
import re
from html import unescape


def scrape_tam_locations(api_url: str = "https://www.tamstore.az/api/branch-api") -> List[Dict[str, str]]:
    """
    Scrape TAM Store branch locations from API

    Args:
        api_url: URL of the TAM Store API endpoint

    Returns:
        List of dictionaries containing branch information
    """
    print(f"Fetching data from {api_url}...")

    try:
        response = requests.get(api_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching API: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        return []

    branches = []

    print("\nExtracting store data from API response...")

    # The API should return a list or dict with branch data
    # Let's handle different possible response structures
    branch_list = []

    if isinstance(data, list):
        branch_list = data
    elif isinstance(data, dict):
        # Try common keys that might contain the branch list
        for key in ['data', 'branches', 'stores', 'locations', 'items']:
            if key in data:
                branch_list = data[key]
                break

        # If still no list found, the dict itself might be the data
        if not branch_list and data:
            branch_list = [data]

    print(f"Found {len(branch_list)} branches in API response")

    for branch in branch_list:
        try:
            # Extract name
            name = branch.get('title', '')

            # Extract and clean address (remove HTML tags)
            address = branch.get('address', '')
            if address:
                # Remove HTML tags
                address = re.sub(r'<[^>]+>', '', address)
                # Unescape HTML entities
                address = unescape(address).strip()

            # Extract phone (use phone_1)
            phone = branch.get('phone_1', '')

            # Extract work hours
            hours = branch.get('work_hours', '')

            # Extract coordinates from map field
            latitude = ''
            longitude = ''
            map_data = branch.get('map', '')

            if map_data:
                # Try to extract coordinates from different formats
                # Format 1: Direct URL like "https://www.google.com/maps?q=41.09286117553711,45.365360260009766"
                coord_match = re.search(r'[?&]q=([-\d.]+),([-\d.]+)', map_data)
                if coord_match:
                    latitude = coord_match.group(1)
                    longitude = coord_match.group(2)
                else:
                    # Format 2: Iframe embed URL with coordinates in a different format
                    # Example: !1m17!1m12!1m3!1d3037.134160954774!2d49.960864976011635!3d40.428028071437765
                    # Look for pattern like !3d{lat} and !2d{lng}
                    lat_match = re.search(r'!3d([-\d.]+)', map_data)
                    lng_match = re.search(r'!2d([-\d.]+)', map_data)
                    if lat_match and lng_match:
                        latitude = lat_match.group(1)
                        longitude = lng_match.group(1)

            branch_data = {
                'name': name,
                'address': address,
                'phone': phone,
                'hours': hours,
                'latitude': latitude,
                'longitude': longitude
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

    fieldnames = ['name', 'address', 'phone', 'hours', 'latitude', 'longitude']

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
    print("TAM Store Branch Scraper")
    print("=" * 60)

    # Scrape data
    branches = scrape_tam_locations()

    if branches:
        # Save to CSV
        output_file = 'data/tam.csv'
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
