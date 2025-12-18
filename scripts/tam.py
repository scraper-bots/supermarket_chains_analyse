#!/usr/bin/env python3
"""
TAM Store Web Scraper
Extracts branch locations and details from tamstore.az API
"""

import csv
import requests
from typing import List, Dict
import os


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
            # Extract fields - adjust these based on actual API response structure
            name = branch.get('name', branch.get('title', branch.get('branch_name', '')))
            address = branch.get('address', branch.get('location', branch.get('full_address', '')))
            phone = branch.get('phone', branch.get('phone_number', branch.get('tel', '')))
            hours = branch.get('hours', branch.get('working_hours', branch.get('work_time', '')))
            latitude = str(branch.get('latitude', branch.get('lat', '')))
            longitude = str(branch.get('longitude', branch.get('lng', branch.get('lon', ''))))

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
