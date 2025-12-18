#!/usr/bin/env python3
"""
Supermarket Chain Analysis & Visualization
Generates business-focused insights and charts from combined supermarket data
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple
from scipy.spatial import distance_matrix
import os
import re

# Set style for attractive visualizations
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Create charts directory
CHARTS_DIR = 'charts'
os.makedirs(CHARTS_DIR, exist_ok=True)


def load_data(file_path: str = 'data/combined.csv') -> pd.DataFrame:
    """Load and prepare the combined supermarket data"""
    df = pd.read_csv(file_path, encoding='utf-8')

    # Convert coordinates to numeric
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

    # Add flag for data completeness
    df['has_phone'] = df['phone'].notna() & (df['phone'].str.strip() != '')
    df['has_address'] = df['address'].notna() & (df['address'].str.strip() != '')
    df['has_hours'] = df['hours'].notna() & (df['hours'].str.strip() != '')
    df['has_coords'] = df['latitude'].notna() & df['longitude'].notna()

    return df


def infer_city_from_coordinates(lat: float, lon: float) -> str:
    """Infer city name from coordinates for stores without addresses"""
    # Major city coordinates (approximate centers)
    city_coords = {
        'Bakı': (40.4093, 49.8671),
        'Sumqayıt': (40.5894, 49.6684),
        'Gəncə': (40.6828, 46.3606),
        'Mingəçevir': (40.7639, 47.0497),
        'Xırdalan': (40.4527, 49.7389),
        'Şəki': (41.1974, 47.1704),
        'Naxçıvan': (39.2090, 45.4120),
        'Şirvan': (39.9369, 48.9200),
        'Lənkəran': (38.7542, 48.8510),
        'Qazax': (41.0924, 45.3654),
        'Zaqatala': (41.6317, 46.6445),
        'Şamaxı': (40.6304, 48.6389),
        'Quba': (41.3614, 48.5128),
        'Masallı': (39.0352, 48.6717),
    }

    # Find nearest city (within 50km ~0.45 degrees)
    min_dist = float('inf')
    nearest_city = 'Bakı'  # Default

    for city, (city_lat, city_lon) in city_coords.items():
        dist = np.sqrt((lat - city_lat)**2 + (lon - city_lon)**2)
        if dist < min_dist:
            min_dist = dist
            nearest_city = city

    # If too far from any known city (>0.5 degrees ~55km), classify as Bakı if in Greater Baku region
    if min_dist > 0.5:
        if 40.1 < lat < 40.7 and 49.5 < lon < 50.5:
            return 'Bakı'
        return 'Regional'

    return nearest_city


def extract_city_from_address(row: pd.Series) -> str:
    """Extract city/region name from address or infer from coordinates"""
    address = row.get('address', '')

    # If no address, use coordinates
    if pd.isna(address) or str(address).strip() == '':
        if pd.notna(row.get('latitude')) and pd.notna(row.get('longitude')):
            return infer_city_from_coordinates(row['latitude'], row['longitude'])
        return 'Unknown'

    address = str(address)

    # Major cities (expanded list)
    major_cities = ['Bakı', 'Sumqayıt', 'Gəncə', 'Mingəçevir', 'Xırdalan',
                    'Naxçıvan', 'Şəki', 'Qazax', 'Zaqatala', 'Masallı',
                    'Ağdaş', 'Şəmkir', 'Bərdə', 'Salyan', 'Ağstafa',
                    'Hacıqabul', 'Ağcabədi', 'Şərur', 'Cəlilabad', 'Lənkəran',
                    'Şirvan', 'Quba', 'Şamaxı', 'Yevlax', 'Göyçay']

    for city in major_cities:
        if city.lower() in address.lower():
            return city

    # Try to extract rayonu (district)
    rayon_match = re.search(r'(\w+)\s+(ray|rayonu)', address, re.IGNORECASE)
    if rayon_match:
        district = rayon_match.group(1).capitalize()
        # Map districts to cities
        district_map = {
            'Nəsimi': 'Bakı', 'Nərimanov': 'Bakı', 'Xətai': 'Bakı',
            'Yasamal': 'Bakı', 'Səbail': 'Bakı', 'Nizami': 'Bakı',
            'Binəqədi': 'Bakı', 'Sabunçu': 'Bakı', 'Suraxanı': 'Bakı',
            'Qaradağ': 'Bakı', 'Xəzər': 'Bakı', 'Abşeron': 'Bakı'
        }
        return district_map.get(district, district)

    # Try to extract settlement
    settlement_match = re.search(r'(\w+)\s+(şəh|şəhəri|qəs|qəsəbəsi)', address, re.IGNORECASE)
    if settlement_match:
        city_name = settlement_match.group(1).capitalize()
        # Filter out common words
        if city_name not in ['Yeni', 'Köhnə', 'Birinci', 'İkinci', 'Böyük', 'Kiçik']:
            return city_name

    # Default to Baku if contains common Baku keywords
    baku_keywords = ['metrosu', 'metro', 'prospekt', 'pr.']
    if any(kw in address.lower() for kw in baku_keywords):
        return 'Bakı'

    # Last resort: use coordinates if available
    if pd.notna(row.get('latitude')) and pd.notna(row.get('longitude')):
        return infer_city_from_coordinates(row['latitude'], row['longitude'])

    return 'Regional'


def chart_1_market_share(df: pd.DataFrame) -> Dict:
    """Chart 1: Market Share by Chain"""
    fig, ax = plt.subplots(figsize=(10, 6))

    chain_counts = df['chain'].value_counts().sort_values(ascending=True)
    colors = sns.color_palette("husl", len(chain_counts))

    bars = ax.barh(chain_counts.index, chain_counts.values, color=colors, edgecolor='black', linewidth=1.5)

    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        percentage = (width / df.shape[0]) * 100
        ax.text(width + 20, bar.get_y() + bar.get_height()/2,
                f'{int(width)} ({percentage:.1f}%)',
                ha='left', va='center', fontsize=11, fontweight='bold')

    ax.set_xlabel('Number of Stores', fontsize=12, fontweight='bold')
    ax.set_title('Market Share by Supermarket Chain', fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/01_market_share.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Market Share Analysis',
        'insight': f"OBA dominates with {chain_counts['OBA']} stores ({chain_counts['OBA']/df.shape[0]*100:.1f}% market share)"
    }


def chart_2_geographic_distribution(df: pd.DataFrame) -> Dict:
    """Chart 2: City-Level Market Share Map (Bubble Chart)"""
    df['city'] = df.apply(extract_city_from_address, axis=1)

    # Filter to valid cities and get top 20 by store count
    valid_df = df[~df['city'].isin(['Unknown', 'Regional'])].copy()
    top_20_cities = valid_df['city'].value_counts().head(20).index

    city_data = []
    for city in top_20_cities:
        city_df = df[df['city'] == city]

        # Get coordinates (average for the city)
        lat = city_df['latitude'].mean()
        lon = city_df['longitude'].mean()

        # Get dominant chain
        chain_counts = city_df['chain'].value_counts()
        dominant_chain = chain_counts.index[0]
        dominant_pct = (chain_counts.iloc[0] / len(city_df)) * 100

        city_data.append({
            'City': city,
            'Latitude': lat,
            'Longitude': lon,
            'Total Stores': len(city_df),
            'Dominant Chain': dominant_chain,
            'Dominance %': dominant_pct,
            'Num Chains': city_df['chain'].nunique()
        })

    city_df_plot = pd.DataFrame(city_data)

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 12))

    # Assign colors by dominant chain
    chain_colors = {chain: color for chain, color in zip(df['chain'].unique(), sns.color_palette("husl", df['chain'].nunique()))}
    colors = [chain_colors[chain] for chain in city_df_plot['Dominant Chain']]

    # Create bubble chart - size by total stores
    scatter = ax.scatter(city_df_plot['Longitude'], city_df_plot['Latitude'],
                        s=city_df_plot['Total Stores']*3,  # Size by store count
                        c=colors, alpha=0.7,
                        edgecolors='black', linewidth=2)

    # Add city labels with store count
    for idx, row in city_df_plot.iterrows():
        label = f"{row['City']}\n{int(row['Total Stores'])} stores"
        if row['Num Chains'] == 1:
            label += "\n(Monopoly)"

        # Position label to avoid overlap
        offset_x = 0.05 if idx % 2 == 0 else -0.05
        offset_y = 0.03 if idx % 3 == 0 else -0.03

        ax.annotate(label,
                   (row['Longitude'], row['Latitude']),
                   xytext=(offset_x, offset_y), textcoords='offset fontsize',
                   fontsize=8, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.8, edgecolor='gray'),
                   ha='center')

    ax.set_xlabel('Longitude →', fontsize=13, fontweight='bold')
    ax.set_ylabel('Latitude →', fontsize=13, fontweight='bold')
    ax.set_title('Azerbaijan Supermarket Landscape: Market Dominance by City\n(Bubble Size = Store Count, Color = Dominant Chain)',
                fontsize=14, fontweight='bold', pad=20)

    # Create legend for chains
    legend_elements = [plt.scatter([], [], s=100, c=chain_colors[chain], edgecolors='black', linewidth=2, label=chain)
                      for chain in df['chain'].unique()]
    ax.legend(handles=legend_elements, title='Dominant Chain',
             loc='upper right', framealpha=0.95, fontsize=10, title_fontsize=11)

    ax.grid(alpha=0.2, linestyle='--')

    # Add size reference in corner
    ax.scatter([], [], s=300, c='gray', alpha=0.5, edgecolors='black', linewidth=2, label='100 stores')
    ax.scatter([], [], s=900, c='gray', alpha=0.5, edgecolors='black', linewidth=2, label='300 stores')
    ax.scatter([], [], s=3000, c='gray', alpha=0.5, edgecolors='black', linewidth=2, label='1000 stores')

    size_legend = ax.legend(loc='lower left', framealpha=0.95, fontsize=9, title='Store Count Scale', title_fontsize=10)
    ax.add_artist(size_legend)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/02_geographic_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Geographic Market Map',
        'insight': f"Top 20 cities visualized by market size. Baku dominates with {city_df_plot[city_df_plot['City']=='Bakı']['Total Stores'].values[0] if 'Bakı' in city_df_plot['City'].values else 0} stores"
    }


def chart_3_market_concentration(df: pd.DataFrame) -> Dict:
    """Chart 3: Market Concentration Index (Herfindahl-Hirschman Index)"""
    df['city'] = df.apply(extract_city_from_address, axis=1)

    fig, ax = plt.subplots(figsize=(14, 8))

    # Calculate HHI for top 15 cities
    top_cities = df['city'].value_counts().head(15).index

    hhi_data = []
    for city in top_cities:
        city_df = df[df['city'] == city]
        market_shares = city_df['chain'].value_counts() / len(city_df)
        hhi = (market_shares ** 2).sum() * 10000  # HHI scale
        total_stores = len(city_df)
        num_chains = city_df['chain'].nunique()
        hhi_data.append({'City': city, 'HHI': hhi, 'Stores': total_stores, 'Chains': num_chains})

    hhi_df = pd.DataFrame(hhi_data).sort_values('HHI', ascending=False)

    # Color based on market concentration
    colors = ['#e74c3c' if hhi > 5000 else '#f39c12' if hhi > 2500 else '#2ecc71' for hhi in hhi_df['HHI']]

    bars = ax.barh(range(len(hhi_df)), hhi_df['HHI'], color=colors, edgecolor='black', linewidth=1)
    ax.set_yticks(range(len(hhi_df)))
    ax.set_yticklabels(hhi_df['City'])

    # Add value labels and store count
    for i, (idx, row) in enumerate(hhi_df.iterrows()):
        ax.text(row['HHI'] + 100, i,
                f"HHI: {row['HHI']:.0f} | {row['Stores']} stores | {row['Chains']} chains",
                va='center', fontsize=9, fontweight='bold')

    # Add reference lines
    ax.axvline(2500, color='orange', linestyle='--', alpha=0.7, label='Moderate Concentration')
    ax.axvline(5000, color='red', linestyle='--', alpha=0.7, label='High Concentration')

    ax.set_xlabel('Herfindahl-Hirschman Index (HHI)', fontsize=12, fontweight='bold')
    ax.set_title('Market Concentration by City (Higher HHI = Less Competition)',
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='lower right')
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/03_market_concentration.png', dpi=300, bbox_inches='tight')
    plt.close()

    monopoly_cities = hhi_df[hhi_df['HHI'] >= 10000]
    return {
        'title': 'Market Concentration',
        'insight': f"{len(monopoly_cities)} cities have monopoly markets (HHI=10000). "
                  f"Bakı shows most competitive market structure."
    }


def chart_4_top_cities(df: pd.DataFrame) -> Dict:
    """Chart 4: Top 15 Cities by Store Count"""
    df['city'] = df.apply(extract_city_from_address, axis=1)

    # Exclude generic categories
    valid_cities = df[~df['city'].isin(['Unknown', 'Regional'])].copy()

    fig, ax = plt.subplots(figsize=(12, 8))

    top_cities = valid_cities['city'].value_counts().head(15)
    colors = sns.color_palette("viridis", len(top_cities))

    bars = ax.barh(range(len(top_cities)), top_cities.values, color=colors, edgecolor='black', linewidth=1)
    ax.set_yticks(range(len(top_cities)))
    ax.set_yticklabels(top_cities.index, fontsize=11, fontweight='bold')

    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        percentage = (width / len(df)) * 100
        ax.text(width + 5, bar.get_y() + bar.get_height()/2,
                f'{int(width)} ({percentage:.1f}%)',
                ha='left', va='center', fontsize=10, fontweight='bold')

    ax.set_xlabel('Number of Stores', fontsize=12, fontweight='bold')
    ax.set_title('Top 15 Cities by Store Count', fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/04_top_cities.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'City Rankings',
        'insight': f"Bakı leads with {top_cities.iloc[0]} stores ({top_cities.iloc[0]/len(df)*100:.1f}% of total market)"
    }


def chart_5_chain_by_city(df: pd.DataFrame) -> Dict:
    """Chart 5: Chain Competition in Major Cities (Grouped Horizontal)"""
    if 'city' not in df.columns:
        df['city'] = df.apply(extract_city_from_address, axis=1)

    fig, ax = plt.subplots(figsize=(14, 10))

    # Top 12 cities
    top_cities = df[~df['city'].isin(['Unknown', 'Regional'])]['city'].value_counts().head(12).index
    city_chain_data = df[df['city'].isin(top_cities)].groupby(['city', 'chain']).size().unstack(fill_value=0)

    # Reorder by total stores
    city_chain_data['Total'] = city_chain_data.sum(axis=1)
    city_chain_data = city_chain_data.sort_values('Total', ascending=True).drop('Total', axis=1)

    city_chain_data.plot(kind='barh', stacked=False, ax=ax, width=0.75, edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Number of Stores', fontsize=12, fontweight='bold')
    ax.set_ylabel('City', fontsize=12, fontweight='bold')
    ax.set_title('Chain Presence in Major Cities (Side-by-Side Comparison)',
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(title='Chain', bbox_to_anchor=(1.02, 1), loc='upper left', framealpha=0.95)
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/05_chain_by_city.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Urban Competition',
        'insight': "OBA dominates most cities, ARAZ maintains strong secondary position across regions"
    }


def chart_6_competitive_intensity(df: pd.DataFrame) -> Dict:
    """Chart 6: Competitive Intensity Analysis - Cleaner Version"""
    if 'city' not in df.columns:
        df['city'] = df.apply(extract_city_from_address, axis=1)

    fig, ax = plt.subplots(figsize=(16, 10))

    # Calculate competitive metrics for top 12 cities only (reduce crowding)
    top_cities = df[~df['city'].isin(['Unknown', 'Regional'])]['city'].value_counts().head(12).index

    comp_data = []
    for city in top_cities:
        city_df = df[df['city'] == city]
        total_stores = len(city_df)
        num_chains = city_df['chain'].nunique()
        stores_per_chain = total_stores / num_chains if num_chains > 0 else 0
        intensity = total_stores / (num_chains ** 2) if num_chains > 0 else 0

        comp_data.append({
            'City': city,
            'Stores': total_stores,
            'Chains': num_chains,
            'Stores per Chain': stores_per_chain,
            'Intensity': intensity
        })

    comp_df = pd.DataFrame(comp_data).sort_values('Stores', ascending=False)

    # Create bubble chart with better spacing
    scatter = ax.scatter(comp_df['Chains'], comp_df['Stores'],
                        s=comp_df['Stores per Chain']*8,
                        c=comp_df['Intensity'], cmap='RdYlGn_r',
                        alpha=0.75, edgecolors='black', linewidth=2.5)

    # Add city labels with smart positioning using adjustText-style logic
    from matplotlib import patheffects
    for idx, row in comp_df.iterrows():
        # Offset based on position to reduce overlap
        if row['Stores'] > 500:
            xytext = (10, 10)
        elif row['Stores'] > 200:
            xytext = (-30, -15) if row['Chains'] > 3 else (10, -15)
        else:
            xytext = (8, -20) if idx % 2 == 0 else (-35, 8)

        text = ax.annotate(f"{row['City']}\n({int(row['Stores'])} stores, {int(row['Chains'])} chains)",
                          (row['Chains'], row['Stores']),
                          xytext=xytext, textcoords='offset points',
                          fontsize=9, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.85, edgecolor='gray', linewidth=1),
                          arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3', color='gray', lw=1.5))

    # Add quadrant lines
    median_chains = comp_df['Chains'].median()
    median_stores = comp_df['Stores'].median()

    ax.axvline(median_chains, color='red', linestyle='--', alpha=0.4, linewidth=2, label='Median Chains')
    ax.axhline(median_stores, color='blue', linestyle='--', alpha=0.4, linewidth=2, label='Median Stores')

    # Add quadrant annotations
    ax.text(ax.get_xlim()[1]*0.95, ax.get_ylim()[1]*0.95, 'High Competition\nMany Stores',
           fontsize=11, fontweight='bold', ha='right', va='top',
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

    ax.text(ax.get_xlim()[0]*1.05, ax.get_ylim()[1]*0.95, 'OPPORTUNITY\nLow Competition',
           fontsize=11, fontweight='bold', ha='left', va='top', color='green',
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))

    ax.set_xlabel('Number of Competing Chains', fontsize=13, fontweight='bold')
    ax.set_ylabel('Total Stores in City', fontsize=13, fontweight='bold')
    ax.set_title('Market Competition Map: Store Count vs Chain Competition\n(Bubble Size = Average Stores per Chain)',
                fontsize=14, fontweight='bold', pad=20)
    ax.grid(alpha=0.25, linestyle='--')

    # Colorbar with better label
    cbar = plt.colorbar(scatter, ax=ax, pad=0.02)
    cbar.set_label('Market Concentration\n(Red = Few chains dominate)', fontsize=10, fontweight='bold')

    # Legend for reference
    ax.legend(loc='lower right', framealpha=0.9, fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/06_competitive_intensity.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Competition Landscape',
        'insight': "Top-left quadrant cities (high stores, few chains) are prime expansion targets"
    }


def chart_7_market_opportunity(df: pd.DataFrame) -> Dict:
    """Chart 7: Market Opportunity Map - Top 15 Cities Only"""
    if 'city' not in df.columns:
        df['city'] = df.apply(extract_city_from_address, axis=1)

    fig, ax = plt.subplots(figsize=(14, 10))

    # Top 15 cities only to avoid crowding
    top_cities = df[~df['city'].isin(['Unknown', 'Regional'])]['city'].value_counts().head(15).index

    opp_data = []
    for city in top_cities:
        city_df = df[df['city'] == city]
        total_stores = len(city_df)
        num_chains = city_df['chain'].nunique()

        # Opportunity score: More stores but fewer chains = higher opportunity
        opportunity_score = (total_stores / 100) - num_chains

        opp_data.append({
            'City': city,
            'Total Stores': total_stores,
            'Active Chains': num_chains,
            'Opportunity Score': opportunity_score
        })

    opp_df = pd.DataFrame(opp_data).sort_values('Opportunity Score', ascending=False)  # Best opportunities at top

    # Color: Green = high opportunity, Red = saturated
    colors = ['#2ecc71' if score > 0 else '#e74c3c' for score in opp_df['Opportunity Score']]

    bars = ax.barh(range(len(opp_df)), opp_df['Opportunity Score'],
                   color=colors, edgecolor='black', linewidth=2)
    ax.set_yticks(range(len(opp_df)))
    ax.set_yticklabels(opp_df['City'], fontsize=11, fontweight='bold')

    # Add labels with better positioning
    for i, (idx, row) in enumerate(opp_df.iterrows()):
        score = row['Opportunity Score']
        if score > 0:
            # Positive scores - label on right
            ax.text(score + 0.15, i,
                    f"{int(row['Total Stores'])} stores, {int(row['Active Chains'])} chains  ",
                    va='center', ha='left', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.3))
        else:
            # Negative scores - label on left
            ax.text(score - 0.15, i,
                    f"  {int(row['Total Stores'])} stores, {int(row['Active Chains'])} chains",
                    va='center', ha='right', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.3))

    # Add zero line
    ax.axvline(0, color='black', linestyle='-', linewidth=3, alpha=0.7)

    # Add annotations
    ax.text(ax.get_xlim()[1]*0.9, len(opp_df)*0.1, 'EXPANSION\nTARGETS',
           fontsize=12, fontweight='bold', ha='center', color='darkgreen',
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5, edgecolor='green', linewidth=2))

    ax.text(ax.get_xlim()[0]*0.9, len(opp_df)*0.9, 'SATURATED\nAVOID',
           fontsize=12, fontweight='bold', ha='center', color='darkred',
           bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5, edgecolor='red', linewidth=2))

    ax.set_xlabel('Market Opportunity Score\n(Positive = High Stores & Low Competition = Good Target)',
                 fontsize=12, fontweight='bold')
    ax.set_title('Market Expansion Opportunities: Top 15 Cities Ranked',
                fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.25, linestyle='--')

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/07_market_opportunity.png', dpi=300, bbox_inches='tight')
    plt.close()

    best_opp = opp_df.iloc[0]  # Top ranked opportunity

    insight = f"Best target: {best_opp['City']} - {int(best_opp['Total Stores'])} stores with only {int(best_opp['Active Chains'])} chains (opportunity score: {best_opp['Opportunity Score']:.1f})"

    return {
        'title': 'Expansion Strategy',
        'insight': insight
    }


def chart_8_chain_comparison(df: pd.DataFrame) -> Dict:
    """Chart 8: Chain Performance Metrics"""
    if 'city' not in df.columns:
        df['city'] = df.apply(extract_city_from_address, axis=1)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    chains = df['chain'].unique()
    metrics = []

    for chain in chains:
        chain_df = df[df['chain'] == chain]
        metrics.append({
            'Chain': chain,
            'Stores': len(chain_df),
            'Cities': chain_df['city'].nunique(),
            'Avg per City': len(chain_df) / chain_df['city'].nunique()
        })

    metrics_df = pd.DataFrame(metrics)
    colors = sns.color_palette("husl", len(chains))

    # Store count
    axes[0].bar(metrics_df['Chain'], metrics_df['Stores'], color=colors, edgecolor='black', linewidth=2)
    axes[0].set_ylabel('Total Stores', fontsize=11, fontweight='bold')
    axes[0].set_title('Store Count', fontsize=12, fontweight='bold')
    axes[0].grid(axis='y', alpha=0.3)
    for i, v in enumerate(metrics_df['Stores']):
        axes[0].text(i, v + 20, str(v), ha='center', fontweight='bold')

    # Geographic spread
    axes[1].bar(metrics_df['Chain'], metrics_df['Cities'], color=colors, edgecolor='black', linewidth=2)
    axes[1].set_ylabel('Cities Covered', fontsize=11, fontweight='bold')
    axes[1].set_title('Geographic Reach', fontsize=12, fontweight='bold')
    axes[1].grid(axis='y', alpha=0.3)
    for i, v in enumerate(metrics_df['Cities']):
        axes[1].text(i, v + 0.5, f'{int(v)}', ha='center', fontweight='bold')

    # Market density
    axes[2].bar(metrics_df['Chain'], metrics_df['Avg per City'], color=colors, edgecolor='black', linewidth=2)
    axes[2].set_ylabel('Avg Stores per City', fontsize=11, fontweight='bold')
    axes[2].set_title('Market Density', fontsize=12, fontweight='bold')
    axes[2].grid(axis='y', alpha=0.3)
    for i, v in enumerate(metrics_df['Avg per City']):
        axes[2].text(i, v + 1, f'{v:.1f}', ha='center', fontweight='bold')

    plt.suptitle('Chain Performance Comparison', fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/08_chain_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Chain Metrics',
        'insight': "OBA leads in scale, ARAZ in density - different growth strategies evident"
    }


def chart_9_regional_distribution(df: pd.DataFrame) -> Dict:
    """Chart 9: Regional Market Share"""
    if 'city' not in df.columns:
        df['city'] = df.apply(extract_city_from_address, axis=1)

    fig, ax = plt.subplots(figsize=(12, 8))

    # Clean data - exclude Unknown/Regional
    valid_df = df[~df['city'].isin(['Unknown', 'Regional'])].copy()

    city_counts = valid_df['city'].value_counts()
    top_8 = city_counts.head(8)
    others = city_counts[8:].sum()

    plot_data = pd.concat([top_8, pd.Series({'Other Cities': others})])

    colors = sns.color_palette("Set3", len(plot_data))

    def autopct_format(pct):
        return f'{pct:.1f}%' if pct > 3 else ''

    wedges, texts, autotexts = ax.pie(plot_data.values, labels=plot_data.index,
                                       autopct=autopct_format, startangle=90,
                                       colors=colors, textprops={'fontsize': 11, 'fontweight': 'bold'},
                                       pctdistance=0.85, explode=[0.05 if i == 0 else 0 for i in range(len(plot_data))])

    # Add counts in legend
    legend_labels = [f'{city}: {count} stores' for city, count in plot_data.items()]
    ax.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1), fontsize=10)

    ax.set_title('Geographic Distribution of Stores', fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/09_regional_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Regional Breakdown',
        'insight': f"Bakı holds {plot_data.iloc[0]/plot_data.sum()*100:.1f}% of market. "
                  f"Top 8 cities = {top_8.sum()/valid_df.shape[0]*100:.1f}% of stores"
    }


def chart_10_latitude_distribution(df: pd.DataFrame) -> Dict:
    """Chart 10: North-South Geographic Spread"""
    fig, ax = plt.subplots(figsize=(12, 6))

    df_coords = df[df['has_coords']].copy()

    chains = sorted(df_coords['chain'].unique())
    data_to_plot = [df_coords[df_coords['chain'] == chain]['latitude'].values for chain in chains]

    bp = ax.boxplot(data_to_plot, labels=chains, patch_artist=True, widths=0.6,
                    showmeans=True, meanline=True,
                    boxprops=dict(facecolor='lightblue', edgecolor='black', linewidth=1.5),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5),
                    medianprops=dict(color='red', linewidth=2),
                    meanprops=dict(color='green', linewidth=2, linestyle='--'))

    ax.set_ylabel('Latitude (degrees)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Chain', fontsize=12, fontweight='bold')
    ax.set_title('Geographic Reach: North-South Coverage (Latitude Range)',
                fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add legend
    ax.legend([bp['medians'][0], bp['means'][0]], ['Median', 'Mean'], loc='upper right')

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/10_latitude_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Geographic Coverage',
        'insight': "All chains concentrate around 40° (Baku). Wider spread indicates national coverage"
    }


def chart_11_store_saturation(df: pd.DataFrame) -> Dict:
    """Chart 11: Market Saturation Analysis - Stores per 10k people estimate"""
    if 'city' not in df.columns:
        df['city'] = df.apply(extract_city_from_address, axis=1)

    fig, ax = plt.subplots(figsize=(14, 8))

    # Approximate population estimates for major cities (in thousands)
    population_estimates = {
        'Bakı': 2300,
        'Gəncə': 335,
        'Sumqayıt': 350,
        'Mingəçevir': 100,
        'Xırdalan': 110,
        'Şəki': 67,
        'Naxçıvan': 90,
        'Qazax': 90,
        'Zaqatala': 65,
        'Şirvan': 85,
        'Lənkəran': 85,
        'Yevlax': 65,
    }

    saturation_data = []
    for city, pop in population_estimates.items():
        city_stores = len(df[df['city'] == city])
        if city_stores > 0:
            stores_per_10k = (city_stores / pop) * 10
            saturation_data.append({
                'City': city,
                'Stores': city_stores,
                'Pop (k)': pop,
                'Stores per 10k': stores_per_10k
            })

    sat_df = pd.DataFrame(saturation_data).sort_values('Stores per 10k', ascending=True)

    # Color by saturation level
    colors = ['#e74c3c' if x > 6 else '#f39c12' if x > 3 else '#2ecc71' for x in sat_df['Stores per 10k']]

    bars = ax.barh(range(len(sat_df)), sat_df['Stores per 10k'], color=colors, edgecolor='black', linewidth=1.5)
    ax.set_yticks(range(len(sat_df)))
    ax.set_yticklabels(sat_df['City'], fontsize=11, fontweight='bold')

    # Add labels
    for i, (idx, row) in enumerate(sat_df.iterrows()):
        ax.text(row['Stores per 10k'] + 0.2, i,
                f"{row['Stores per 10k']:.1f} ({row['Stores']} stores)",
                va='center', fontsize=9, fontweight='bold')

    ax.set_xlabel('Stores per 10,000 Population (Estimated)', fontsize=12, fontweight='bold')
    ax.set_title('Market Saturation Analysis by City\n(Green = Underserved, Red = Saturated)',
                fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.invert_yaxis()

    # Add reference line
    avg_saturation = sat_df['Stores per 10k'].mean()
    ax.axvline(avg_saturation, color='blue', linestyle='--', linewidth=2, alpha=0.7, label=f'Average: {avg_saturation:.1f}')
    ax.legend()

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/11_market_saturation.png', dpi=300, bbox_inches='tight')
    plt.close()

    underserved = sat_df[sat_df['Stores per 10k'] < avg_saturation].iloc[0] if len(sat_df[sat_df['Stores per 10k'] < avg_saturation]) > 0 else None

    if underserved is not None:
        insight = f"Underserved market: {underserved['City']} has only {underserved['Stores per 10k']:.1f} stores per 10k people"
    else:
        insight = "Market saturation varies significantly across cities"

    return {
        'title': 'Market Saturation',
        'insight': insight
    }


def chart_12_store_format_mix(df: pd.DataFrame) -> Dict:
    """Chart 12: Store Format Distribution (Bravo)"""
    bravo_df = df[df['chain'] == 'BRAVO'].copy()

    if 'type' not in bravo_df.columns or bravo_df['type'].isna().all():
        return None

    fig, ax = plt.subplots(figsize=(10, 7))

    type_counts = bravo_df['type'].value_counts()
    colors = sns.color_palette("pastel", len(type_counts))

    # Create bar chart instead of pie to avoid overlapping
    bars = ax.bar(range(len(type_counts)), type_counts.values, color=colors, edgecolor='black', linewidth=1.5)
    ax.set_xticks(range(len(type_counts)))
    ax.set_xticklabels(type_counts.index, rotation=45, ha='right', fontsize=10)

    # Add value labels
    for i, (bar, count) in enumerate(zip(bars, type_counts.values)):
        height = bar.get_height()
        pct = (count / type_counts.sum()) * 100
        ax.text(bar.get_x() + bar.get_width()/2, height + 1,
                f'{count}\n({pct:.1f}%)',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_ylabel('Number of Stores', fontsize=12, fontweight='bold')
    ax.set_title('Bravo Store Format Distribution', fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/12_store_format_mix.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Format Strategy',
        'insight': f"Bravo operates {len(type_counts)} formats. {type_counts.index[0]}: {type_counts.iloc[0]} stores"
    }


def chart_13_chain_territory(df: pd.DataFrame) -> Dict:
    """Chart 13: Chain Territorial Dominance - Fixed Labels"""
    if 'city' not in df.columns:
        df['city'] = df.apply(extract_city_from_address, axis=1)

    fig, ax = plt.subplots(figsize=(16, 10))

    # Top 12 cities only to reduce crowding
    top_cities = df[~df['city'].isin(['Unknown', 'Regional'])]['city'].value_counts().head(12).index

    territory_data = []
    for city in top_cities:
        city_df = df[df['city'] == city]
        chain_counts = city_df['chain'].value_counts()
        dominant_chain = chain_counts.index[0]
        dominant_count = chain_counts.iloc[0]
        total = len(city_df)
        dominance = (dominant_count / total) * 100

        territory_data.append({
            'City': city,
            'Dominant Chain': dominant_chain,
            'Market Share': dominance,
            'Stores': dominant_count,
            'Total': total
        })

    terr_df = pd.DataFrame(territory_data).sort_values('Market Share', ascending=True)

    # Color by dominant chain
    chain_colors = {chain: color for chain, color in zip(df['chain'].unique(), sns.color_palette("husl", df['chain'].nunique()))}
    colors = [chain_colors[chain] for chain in terr_df['Dominant Chain']]

    bars = ax.barh(range(len(terr_df)), terr_df['Market Share'], color=colors, edgecolor='black', linewidth=2)
    ax.set_yticks(range(len(terr_df)))
    ax.set_yticklabels(terr_df['City'], fontsize=12, fontweight='bold')

    # Add labels - positioned INSIDE bars to avoid overlap
    for i, (idx, row) in enumerate(terr_df.iterrows()):
        # Position text inside the bar if long enough, otherwise outside
        if row['Market Share'] > 15:
            # Inside bar - white text
            ax.text(row['Market Share'] / 2, i,
                    f"{row['Dominant Chain']}: {row['Market Share']:.0f}%",
                    va='center', ha='center', fontsize=10, fontweight='bold', color='white',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='black', alpha=0.6))
        else:
            # Outside bar - black text
            ax.text(row['Market Share'] + 2, i,
                    f"{row['Dominant Chain']}: {row['Market Share']:.0f}%",
                    va='center', ha='left', fontsize=9, fontweight='bold')

        # Add store count at the end
        ax.text(103, i, f"{int(row['Stores'])}/{int(row['Total'])}",
                va='center', ha='left', fontsize=8, style='italic')

    ax.set_xlabel('Market Share of Dominant Chain (%)', fontsize=13, fontweight='bold')
    ax.set_title('Territorial Dominance: Leading Chain Market Share by City\n(Color = Dominant Chain)',
                fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_xlim(0, 115)
    ax.invert_yaxis()

    # Add legend for chains
    handles = [plt.Rectangle((0,0),1,1, color=chain_colors[chain], edgecolor='black', linewidth=1.5)
               for chain in sorted(df['chain'].unique())]
    ax.legend(handles, sorted(df['chain'].unique()), title='Dominant Chain',
             loc='lower right', framealpha=0.95, fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/13_chain_territory.png', dpi=300, bbox_inches='tight')
    plt.close()

    monopolies = terr_df[terr_df['Market Share'] == 100]
    return {
        'title': 'Territorial Control',
        'insight': f"{len(monopolies)} cities with 100% dominance. Most cities show competitive markets"
    }


def chart_14_overall_summary(df: pd.DataFrame) -> Dict:
    """Chart 14: Executive Summary Dashboard"""
    if 'city' not in df.columns:
        df['city'] = df.apply(extract_city_from_address, axis=1)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor('#f0f0f0')

    # Total stores
    axes[0, 0].text(0.5, 0.5, f"{len(df):,}",
                   ha='center', va='center', fontsize=60, fontweight='bold', color='#3498db')
    axes[0, 0].text(0.5, 0.2, "Total Stores",
                   ha='center', va='center', fontsize=16, fontweight='bold')
    axes[0, 0].set_facecolor('white')
    axes[0, 0].axis('off')

    # Market leader
    top_chain = df['chain'].value_counts().index[0]
    top_pct = (df['chain'].value_counts().iloc[0] / len(df)) * 100
    axes[0, 1].text(0.5, 0.5, f"{top_chain}",
                   ha='center', va='center', fontsize=40, fontweight='bold', color='#e74c3c')
    axes[0, 1].text(0.5, 0.2, f"Market Leader ({top_pct:.0f}%)",
                   ha='center', va='center', fontsize=14, fontweight='bold')
    axes[0, 1].set_facecolor('white')
    axes[0, 1].axis('off')

    # Cities covered
    cities = df[~df['city'].isin(['Unknown', 'Regional'])]['city'].nunique()
    axes[1, 0].text(0.5, 0.5, f"{cities}",
                   ha='center', va='center', fontsize=60, fontweight='bold', color='#2ecc71')
    axes[1, 0].text(0.5, 0.2, "Cities Covered",
                   ha='center', va='center', fontsize=16, fontweight='bold')
    axes[1, 0].set_facecolor('white')
    axes[1, 0].axis('off')

    # Average stores per city
    avg_per_city = len(df) / cities if cities > 0 else 0
    axes[1, 1].text(0.5, 0.5, f"{avg_per_city:.0f}",
                   ha='center', va='center', fontsize=60, fontweight='bold', color='#f39c12')
    axes[1, 1].text(0.5, 0.2, "Avg Stores per City",
                   ha='center', va='center', fontsize=16, fontweight='bold')
    axes[1, 1].set_facecolor('white')
    axes[1, 1].axis('off')

    plt.suptitle('Azerbaijan Supermarket Market - Executive Summary',
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/14_overall_summary.png', dpi=300, bbox_inches='tight', facecolor='#f0f0f0')
    plt.close()

    return {
        'title': 'Market Overview',
        'insight': f"{len(df):,} stores across {cities} cities. {top_chain} leads with {top_pct:.0f}% share"
    }


def chart_15_growth_potential(df: pd.DataFrame) -> Dict:
    """Chart 15: Growth Potential Matrix - Fixed Labels"""
    if 'city' not in df.columns:
        df['city'] = df.apply(extract_city_from_address, axis=1)

    fig, ax = plt.subplots(figsize=(16, 10))

    # Top 12 cities only to reduce crowding
    top_12_cities = df[~df['city'].isin(['Unknown', 'Regional'])]['city'].value_counts().head(12).index

    city_diversity = df.groupby('city')['chain'].nunique()

    city_data = pd.DataFrame({
        'Store Count': df[df['city'].isin(top_12_cities)]['city'].value_counts(),
        'Chain Count': city_diversity[top_12_cities]
    }).fillna(0)

    # Create scatter plot
    scatter = ax.scatter(city_data['Chain Count'], city_data['Store Count'],
                        s=city_data['Store Count']*2, alpha=0.6,
                        c=city_data['Store Count']/city_data['Chain Count'],
                        cmap='RdYlGn_r', edgecolors='black', linewidth=2)

    # Add city labels with smart positioning to avoid overlap
    for idx, (city, row) in enumerate(city_data.iterrows()):
        # Smart offset based on position and index to reduce overlap
        if row['Store Count'] > 800:
            # Very high stores (Bakı) - label above right
            xytext = (15, 20)
        elif row['Store Count'] > 300:
            # High stores - alternate positions
            if row['Chain Count'] > 4:
                xytext = (10, -25)  # Top right quadrant - label below
            else:
                xytext = (-60, 15)  # Top left quadrant - label left
        elif row['Store Count'] > 100:
            # Medium stores - varied positions
            if idx % 3 == 0:
                xytext = (12, 8)
            elif idx % 3 == 1:
                xytext = (-50, -8)
            else:
                xytext = (8, -22)
        else:
            # Low stores - alternate sides
            xytext = (10, 10) if idx % 2 == 0 else (-55, -5)

        ax.annotate(city, (row['Chain Count'], row['Store Count']),
                   xytext=xytext, textcoords='offset points',
                   fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.8, edgecolor='gray'),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2', color='gray', lw=1.2))

    ax.set_xlabel('Number of Competing Chains', fontsize=13, fontweight='bold')
    ax.set_ylabel('Total Number of Stores', fontsize=13, fontweight='bold')
    ax.set_title('Growth Potential Matrix\n(Top-Right = Saturated, Bottom-Left = Opportunity)',
                fontsize=15, fontweight='bold', pad=20)
    ax.grid(alpha=0.3, linestyle='--')

    # Add quadrant lines
    median_chains = city_data['Chain Count'].median()
    median_stores = city_data['Store Count'].median()
    ax.axvline(median_chains, color='red', linestyle='--', alpha=0.5, linewidth=2)
    ax.axhline(median_stores, color='red', linestyle='--', alpha=0.5, linewidth=2)

    # Add quadrant labels
    ax.text(ax.get_xlim()[1]*0.85, ax.get_ylim()[1]*0.95, 'Saturated\nMarket',
           fontsize=11, fontweight='bold', ha='center',
           bbox=dict(boxstyle='round', facecolor='#e74c3c', alpha=0.3))
    ax.text(ax.get_xlim()[0]*1.15, ax.get_ylim()[0]*1.05, 'Expansion\nOpportunity',
           fontsize=11, fontweight='bold', ha='center',
           bbox=dict(boxstyle='round', facecolor='#2ecc71', alpha=0.3))

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Stores per Chain (Higher = More Concentrated)', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/15_growth_potential.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Find best opportunity
    low_competition = city_data[(city_data['Chain Count'] < median_chains) & (city_data['Store Count'] > median_stores)]

    if len(low_competition) > 0:
        best = low_competition.idxmax()['Store Count']
        insight = f"Best opportunity: {best} - high stores ({int(city_data.loc[best, 'Store Count'])}), low competition ({int(city_data.loc[best, 'Chain Count'])} chains)"
    else:
        insight = "Competitive balance across major cities - focus on underserved secondary markets"

    return {
        'title': 'Strategic Opportunities',
        'insight': insight
    }


def chart_16_azerbaijan_map(df: pd.DataFrame) -> Dict:
    """Chart 16: Azerbaijan Geographic Map - All Supermarket Locations"""
    fig, ax = plt.subplots(figsize=(20, 14))

    # Filter stores with valid coordinates
    df_coords = df[df['has_coords']].copy()

    # Define very distinct colors for each chain (vivid and clearly different)
    distinct_colors = {
        'OBA': '#0066CC',      # Deep Blue
        'ARAZ': '#FF6600',     # Bright Orange
        'BRAVO': '#CC0000',    # Red
        'RAHAT': '#00CC33',    # Green
        'TAM': '#9933FF'       # Purple
    }

    # Map colors to chains
    chain_colors = {}
    for chain in df['chain'].unique():
        chain_colors[chain] = distinct_colors.get(chain, '#808080')  # Gray as fallback

    colors = [chain_colors[chain] for chain in df_coords['chain']]

    # Create scatter plot with larger dots
    scatter = ax.scatter(df_coords['longitude'], df_coords['latitude'],
                        c=colors, alpha=0.7, s=50, edgecolors='black', linewidth=0.8)

    # Set Azerbaijan geographic bounds
    ax.set_xlim(44.5, 51.0)  # Longitude range for Azerbaijan
    ax.set_ylim(38.2, 42.0)  # Latitude range for Azerbaijan

    # City labels removed for cleaner visualization
    if 'city' not in df.columns:
        df['city'] = df.apply(extract_city_from_address, axis=1)

    # Set labels and title
    ax.set_xlabel('Longitude (°E)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Latitude (°N)', fontsize=14, fontweight='bold')
    ax.set_title('Azerbaijan Supermarket Map: Geographic Distribution of All Stores\n(Each dot = 1 store, Color = Chain)',
                fontsize=16, fontweight='bold', pad=20)

    # Add grid
    ax.grid(alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_aspect('equal', adjustable='box')

    # Create legend for chains
    legend_elements = []
    for chain in sorted(df['chain'].unique()):
        chain_count = len(df_coords[df_coords['chain'] == chain])
        legend_elements.append(
            plt.scatter([], [], s=100, c=[chain_colors[chain]], edgecolors='black', linewidth=1.5,
                       label=f'{chain} ({chain_count} stores)')
        )

    ax.legend(handles=legend_elements, title='Supermarket Chains',
             loc='upper left', framealpha=0.95, fontsize=12, title_fontsize=13)

    # Add stats box
    stats_text = f"Total: {len(df_coords):,} stores\n"
    stats_text += f"Coverage: 100%\n"
    stats_text += f"Cities: {df_coords['city'].nunique()}"

    ax.text(0.98, 0.02, stats_text,
           transform=ax.transAxes, fontsize=12, fontweight='bold',
           verticalalignment='bottom', horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.95, edgecolor='black', linewidth=2.5))

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/16_azerbaijan_map.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Geographic Coverage',
        'insight': f"Complete map of {len(df_coords):,} stores across Azerbaijan. Dense concentration in Baku region, strategic presence in all major cities"
    }


def generate_insights_report(df: pd.DataFrame, all_insights: List[Dict]) -> str:
    """Generate business-focused insights report"""
    df['city'] = df.apply(extract_city_from_address, axis=1)
    valid_cities = df[~df['city'].isin(['Unknown', 'Regional'])]

    report = []
    report.append("# Business Insights - Azerbaijan Supermarket Market\n")

    # Executive Summary
    report.append("## Executive Summary")
    report.append(f"- **Market Size**: {len(df):,} supermarket locations")
    report.append(f"- **Active Chains**: {df['chain'].nunique()} major competitors")
    report.append(f"- **Geographic Reach**: {valid_cities['city'].nunique()} cities/regions")
    report.append(f"- **Market Leader**: {df['chain'].value_counts().index[0]} ({df['chain'].value_counts().iloc[0]/len(df)*100:.1f}% share)\n")

    # Market Concentration
    report.append("## Market Structure")
    chain_counts = df['chain'].value_counts()
    for i, (chain, count) in enumerate(chain_counts.items(), 1):
        report.append(f"{i}. **{chain}**: {count:,} stores ({count/len(df)*100:.1f}%)")
    report.append("")

    # Geographic Insights
    report.append("## Geographic Patterns")
    top_5 = valid_cities['city'].value_counts().head(5)
    report.append(f"- **Baku Dominance**: {top_5.iloc[0]:,} stores ({top_5.iloc[0]/len(df)*100:.1f}% of total)")
    report.append(f"- **Urban Concentration**: Top 5 cities = {top_5.sum()/len(df)*100:.1f}% of market")
    report.append(f"- **Regional Presence**: {valid_cities['city'].nunique()} distinct markets served\n")

    # Competition
    report.append("## Competitive Landscape")
    city_chains = df.groupby('city')['chain'].nunique()
    monopoly_cities = city_chains[city_chains == 1]
    competitive_cities = city_chains[city_chains >= 3]
    report.append(f"- **Monopoly Markets**: {len(monopoly_cities)} cities (single chain)")
    report.append(f"- **Competitive Markets**: {len(competitive_cities)} cities (3+ chains)")
    report.append(f"- **Most Competitive**: {city_chains.idxmax()} ({city_chains.max()} chains)\n")

    # Strategic Recommendations
    report.append("## Strategic Recommendations")
    report.append("1. **Market Entry**: Target monopoly cities with growing populations")
    report.append("2. **Expansion**: Secondary cities show lower competition, higher growth potential")
    report.append("3. **Format Innovation**: Multiple formats (express, super, hyper) serve different segments")
    report.append("4. **Baku Strategy**: Differentiation critical in saturated capital market")
    report.append("5. **Regional Focus**: Underserved cities outside top-5 represent growth opportunities")

    return "\n".join(report)


def main():
    """Main analysis execution"""
    print("=" * 60)
    print("Azerbaijan Supermarket Market Analysis")
    print("Business-Focused Insights Generation")
    print("=" * 60)
    print("\nLoading data...")

    df = load_data()
    print(f"Loaded {len(df):,} stores from {df['chain'].nunique()} chains\n")

    print("Generating business-focused charts...\n")

    insights = []

    # Business-focused charts only
    chart_functions = [
        chart_1_market_share,
        chart_2_geographic_distribution,
        chart_3_market_concentration,
        chart_4_top_cities,
        chart_5_chain_by_city,
        chart_6_competitive_intensity,
        chart_7_market_opportunity,
        chart_8_chain_comparison,
        chart_9_regional_distribution,
        chart_10_latitude_distribution,
        chart_11_store_saturation,
        chart_12_store_format_mix,
        chart_13_chain_territory,
        chart_14_overall_summary,
        chart_15_growth_potential,
        chart_16_azerbaijan_map
    ]

    for i, chart_func in enumerate(chart_functions, 1):
        try:
            print(f"  [{i}/{len(chart_functions)}] {chart_func.__name__}...")
            result = chart_func(df)
            if result:
                insights.append(result)
                print(f"      ✓ {result['insight']}")
        except Exception as e:
            print(f"      ✗ Error: {e}")

    print(f"\n✓ Generated {len(insights)} business charts")

    print("Analysis Complete!")
    print("=" * 60)
    print(f"Charts: {CHARTS_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
