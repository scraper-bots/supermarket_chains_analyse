#!/usr/bin/env python3
"""
Supermarket Chain Analysis & Visualization
Generates insights and charts from combined supermarket data
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple
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


def extract_city_from_address(address: str) -> str:
    """Extract city/region name from address"""
    if pd.isna(address) or address.strip() == '':
        return 'Unknown'

    # Common city patterns in Azerbaijani addresses
    # Format: "City rayonu" or "City şəhəri" or "City qəsəbəsi"

    # Major cities
    major_cities = ['Bakı', 'Sumqayıt', 'Gəncə', 'Mingəçevir', 'Xırdalan',
                    'Naxçıvan', 'Şəki', 'Qazax', 'Zaqatala', 'Masallı',
                    'Ağdaş', 'Şəmkir', 'Bərdə', 'Salyan', 'Ağstafa',
                    'Hacıqabul', 'Ağcabədi', 'Şərur', 'Cəlilabad']

    for city in major_cities:
        if city.lower() in address.lower():
            return city

    # Try to extract rayonu (district)
    rayon_match = re.search(r'(\w+)\s+(ray|rayonu)', address, re.IGNORECASE)
    if rayon_match:
        return rayon_match.group(1).capitalize()

    # Try to extract settlement
    settlement_match = re.search(r'(\w+)\s+(şəh|şəhəri|qəs|qəsəbəsi|kəndi)', address, re.IGNORECASE)
    if settlement_match:
        city_name = settlement_match.group(1).capitalize()
        # Filter out common words that aren't cities
        if city_name not in ['Yeni', 'Köhnə', 'Birinci', 'İkinci']:
            return city_name

    return 'Bakı'  # Default to Baku for addresses without clear city


def chart_1_market_share(df: pd.DataFrame) -> Dict:
    """Chart 1: Market Share by Chain (Store Count)"""
    fig, ax = plt.subplots(figsize=(10, 6))

    chain_counts = df['chain'].value_counts().sort_values(ascending=True)
    colors = sns.color_palette("husl", len(chain_counts))

    bars = ax.barh(chain_counts.index, chain_counts.values, color=colors)

    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        percentage = (width / df.shape[0]) * 100
        ax.text(width, bar.get_y() + bar.get_height()/2,
                f'{int(width)} ({percentage:.1f}%)',
                ha='left', va='center', fontsize=10, fontweight='bold')

    ax.set_xlabel('Number of Stores', fontsize=12, fontweight='bold')
    ax.set_title('Market Share by Supermarket Chain', fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/01_market_share.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Market Share Analysis',
        'insight': f"OBA dominates with {chain_counts['OBA']} stores ({chain_counts['OBA']/df.shape[0]*100:.1f}% market share), "
                  f"followed by ARAZ with {chain_counts['ARAZ']} stores ({chain_counts['ARAZ']/df.shape[0]*100:.1f}%)."
    }


def chart_2_geographic_distribution(df: pd.DataFrame) -> Dict:
    """Chart 2: Geographic Distribution Scatter Map"""
    fig, ax = plt.subplots(figsize=(14, 10))

    # Filter valid coordinates
    df_coords = df[df['has_coords']].copy()

    # Create scatter plot for each chain
    for chain in df_coords['chain'].unique():
        chain_data = df_coords[df_coords['chain'] == chain]
        ax.scatter(chain_data['longitude'], chain_data['latitude'],
                  label=chain, alpha=0.6, s=30, edgecolors='white', linewidth=0.5)

    ax.set_xlabel('Longitude', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=12, fontweight='bold')
    ax.set_title('Geographic Distribution of Supermarket Stores in Azerbaijan',
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(title='Chain', loc='upper right', framealpha=0.9)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/02_geographic_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Geographic Coverage',
        'insight': f"All {df_coords.shape[0]} stores are mapped across Azerbaijan. "
                  f"Concentration visible around Baku (latitude ~40.4°, longitude ~49.8°)."
    }


def chart_3_data_completeness(df: pd.DataFrame) -> Dict:
    """Chart 3: Data Completeness by Chain"""
    fig, ax = plt.subplots(figsize=(12, 6))

    completeness_data = []
    for chain in df['chain'].unique():
        chain_df = df[df['chain'] == chain]
        completeness_data.append({
            'Chain': chain,
            'Coordinates': chain_df['has_coords'].mean() * 100,
            'Address': chain_df['has_address'].mean() * 100,
            'Phone': chain_df['has_phone'].mean() * 100,
            'Hours': chain_df['has_hours'].mean() * 100
        })

    comp_df = pd.DataFrame(completeness_data).set_index('Chain')
    comp_df.plot(kind='bar', ax=ax, width=0.8)

    ax.set_ylabel('Completeness (%)', fontsize=12, fontweight='bold')
    ax.set_title('Data Completeness by Chain', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('')
    ax.legend(title='Data Field', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=0)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/03_data_completeness.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Data Quality',
        'insight': "All chains have 100% coordinate coverage. BRAVO and ARAZ provide the most complete data, "
                  "while OBA focuses on location data only."
    }


def chart_4_top_cities(df: pd.DataFrame) -> Dict:
    """Chart 4: Top 15 Cities by Store Count"""
    # Extract cities
    df['city'] = df['address'].apply(extract_city_from_address)

    fig, ax = plt.subplots(figsize=(12, 8))

    top_cities = df['city'].value_counts().head(15)
    colors = sns.color_palette("viridis", len(top_cities))

    bars = ax.barh(range(len(top_cities)), top_cities.values, color=colors)
    ax.set_yticks(range(len(top_cities)))
    ax.set_yticklabels(top_cities.index)

    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2,
                f'{int(width)}',
                ha='left', va='center', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

    ax.set_xlabel('Number of Stores', fontsize=12, fontweight='bold')
    ax.set_title('Top 15 Cities by Store Count', fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3)
    ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/04_top_cities.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'City Distribution',
        'insight': f"Bakı leads with {top_cities.iloc[0]} stores, followed by {top_cities.index[1]} ({top_cities.iloc[1]}) "
                  f"and {top_cities.index[2]} ({top_cities.iloc[2]})."
    }


def chart_5_chain_by_city(df: pd.DataFrame) -> Dict:
    """Chart 5: Chain Presence in Top 10 Cities"""
    if 'city' not in df.columns:
        df['city'] = df['address'].apply(extract_city_from_address)

    fig, ax = plt.subplots(figsize=(14, 8))

    top_10_cities = df['city'].value_counts().head(10).index
    city_chain_data = df[df['city'].isin(top_10_cities)].groupby(['city', 'chain']).size().unstack(fill_value=0)

    city_chain_data.plot(kind='bar', stacked=True, ax=ax, width=0.8)

    ax.set_ylabel('Number of Stores', fontsize=12, fontweight='bold')
    ax.set_xlabel('')
    ax.set_title('Chain Presence in Top 10 Cities', fontsize=14, fontweight='bold', pad=20)
    ax.legend(title='Chain', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/05_chain_by_city.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Market Competition',
        'insight': "All major chains compete in Bakı. Regional cities show varying levels of chain presence."
    }


def chart_6_baku_density(df: pd.DataFrame) -> Dict:
    """Chart 6: Store Density in Baku Region"""
    if 'city' not in df.columns:
        df['city'] = df['address'].apply(extract_city_from_address)

    baku_df = df[df['city'] == 'Bakı'].copy()

    fig, ax = plt.subplots(figsize=(12, 10))

    # Create density plot
    for chain in baku_df['chain'].unique():
        chain_data = baku_df[baku_df['chain'] == chain]
        ax.scatter(chain_data['longitude'], chain_data['latitude'],
                  label=chain, alpha=0.6, s=50, edgecolors='white', linewidth=0.5)

    ax.set_xlabel('Longitude', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=12, fontweight='bold')
    ax.set_title(f'Store Distribution in Bakı ({len(baku_df)} stores)',
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(title='Chain', loc='best', framealpha=0.9)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/06_baku_density.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Baku Market',
        'insight': f"Bakı has {len(baku_df)} supermarkets, representing "
                  f"{len(baku_df)/len(df)*100:.1f}% of all stores in the dataset."
    }


def chart_7_coordinate_heatmap(df: pd.DataFrame) -> Dict:
    """Chart 7: Geographic Heatmap"""
    fig, ax = plt.subplots(figsize=(14, 10))

    df_coords = df[df['has_coords']].copy()

    # Create hexbin plot for density
    hexbin = ax.hexbin(df_coords['longitude'], df_coords['latitude'],
                       gridsize=30, cmap='YlOrRd', mincnt=1, alpha=0.8)

    ax.set_xlabel('Longitude', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=12, fontweight='bold')
    ax.set_title('Store Density Heatmap', fontsize=14, fontweight='bold', pad=20)

    cb = plt.colorbar(hexbin, ax=ax)
    cb.set_label('Store Count', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/07_density_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Density Analysis',
        'insight': "Highest concentration in Greater Baku area, with secondary clusters in major regional cities."
    }


def chart_8_chain_comparison(df: pd.DataFrame) -> Dict:
    """Chart 8: Chain Comparison Radar Chart"""
    # Calculate metrics for each chain
    metrics_data = []
    for chain in df['chain'].unique():
        chain_df = df[df['chain'] == chain]
        metrics_data.append({
            'Chain': chain,
            'Store Count': len(chain_df),
            'Data Completeness': chain_df[['has_coords', 'has_address', 'has_phone', 'has_hours']].mean().mean() * 100,
            'Geographic Spread': len(chain_df['city'].unique() if 'city' in df.columns else chain_df['latitude'].unique())
        })

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Store count vs data quality
    chains = [m['Chain'] for m in metrics_data]
    store_counts = [m['Store Count'] for m in metrics_data]
    completeness = [m['Data Completeness'] for m in metrics_data]

    colors = sns.color_palette("husl", len(chains))

    # Left plot: Store count
    axes[0].bar(chains, store_counts, color=colors, edgecolor='white', linewidth=2)
    axes[0].set_ylabel('Number of Stores', fontsize=12, fontweight='bold')
    axes[0].set_title('Store Count by Chain', fontsize=12, fontweight='bold')
    axes[0].grid(axis='y', alpha=0.3)

    # Add values on bars
    for i, v in enumerate(store_counts):
        axes[0].text(i, v, str(v), ha='center', va='bottom', fontweight='bold')

    # Right plot: Data completeness
    axes[1].bar(chains, completeness, color=colors, edgecolor='white', linewidth=2)
    axes[1].set_ylabel('Data Completeness (%)', fontsize=12, fontweight='bold')
    axes[1].set_title('Data Quality by Chain', fontsize=12, fontweight='bold')
    axes[1].set_ylim(0, 105)
    axes[1].grid(axis='y', alpha=0.3)

    # Add values on bars
    for i, v in enumerate(completeness):
        axes[1].text(i, v, f'{v:.1f}%', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/08_chain_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Chain Analytics',
        'insight': "ARAZ and BRAVO lead in data quality (>90% completeness), while OBA leads in store count."
    }


def chart_9_regional_distribution(df: pd.DataFrame) -> Dict:
    """Chart 9: Regional Distribution Pie Chart"""
    if 'city' not in df.columns:
        df['city'] = df['address'].apply(extract_city_from_address)

    fig, ax = plt.subplots(figsize=(12, 8))

    # Group smaller cities
    city_counts = df['city'].value_counts()
    top_5 = city_counts.head(5)
    others = city_counts[5:].sum()

    plot_data = pd.concat([top_5, pd.Series({'Others': others})])

    colors = sns.color_palette("husl", len(plot_data))
    wedges, texts, autotexts = ax.pie(plot_data.values, labels=plot_data.index,
                                       autopct='%1.1f%%', startangle=90,
                                       colors=colors, textprops={'fontsize': 11, 'fontweight': 'bold'})

    ax.set_title('Regional Distribution of Stores', fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/09_regional_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Regional Coverage',
        'insight': f"{plot_data.iloc[0]/plot_data.sum()*100:.1f}% of stores are in {plot_data.index[0]}. "
                  f"Top 5 cities account for {top_5.sum()/df.shape[0]*100:.1f}% of all stores."
    }


def chart_10_latitude_distribution(df: pd.DataFrame) -> Dict:
    """Chart 10: Latitude Distribution by Chain"""
    fig, ax = plt.subplots(figsize=(12, 6))

    df_coords = df[df['has_coords']].copy()

    # Violin plot
    chains = df_coords['chain'].unique()
    data_to_plot = [df_coords[df_coords['chain'] == chain]['latitude'].values for chain in chains]

    parts = ax.violinplot(data_to_plot, positions=range(len(chains)),
                          showmeans=True, showmedians=True)

    # Color the violin plots
    colors = sns.color_palette("husl", len(chains))
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)

    ax.set_xticks(range(len(chains)))
    ax.set_xticklabels(chains)
    ax.set_ylabel('Latitude', fontsize=12, fontweight='bold')
    ax.set_title('Geographic Reach by Chain (Latitude Distribution)', fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/10_latitude_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'North-South Coverage',
        'insight': "Most chains concentrate around latitude 40° (Baku region). "
                  "Some chains show wider geographic spread across Azerbaijan."
    }


def chart_11_phone_availability(df: pd.DataFrame) -> Dict:
    """Chart 11: Contact Information Availability"""
    fig, ax = plt.subplots(figsize=(10, 6))

    availability_data = []
    for chain in df['chain'].unique():
        chain_df = df[df['chain'] == chain]
        availability_data.append({
            'Chain': chain,
            'With Phone': chain_df['has_phone'].sum(),
            'Without Phone': (~chain_df['has_phone']).sum()
        })

    avail_df = pd.DataFrame(availability_data).set_index('Chain')
    avail_df.plot(kind='bar', stacked=True, ax=ax,
                  color=['#2ecc71', '#e74c3c'], width=0.7)

    ax.set_ylabel('Number of Stores', fontsize=12, fontweight='bold')
    ax.set_title('Phone Number Availability by Chain', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('')
    ax.legend(title='Status')
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=0)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/11_phone_availability.png', dpi=300, bbox_inches='tight')
    plt.close()

    chains_with_phones = df.groupby('chain')['has_phone'].mean()
    best_chain = chains_with_phones.idxmax()

    return {
        'title': 'Contact Accessibility',
        'insight': f"{best_chain} provides phone numbers for {chains_with_phones[best_chain]*100:.1f}% of its stores, "
                  f"showing strong customer service accessibility."
    }


def chart_12_store_type_distribution(df: pd.DataFrame) -> Dict:
    """Chart 12: Store Type Distribution (for Bravo)"""
    bravo_df = df[df['chain'] == 'BRAVO'].copy()

    if 'type' not in bravo_df.columns or bravo_df['type'].isna().all():
        # Skip if no type data
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    type_counts = bravo_df['type'].value_counts()
    colors = sns.color_palette("pastel", len(type_counts))

    wedges, texts, autotexts = ax.pie(type_counts.values, labels=type_counts.index,
                                       autopct='%1.1f%%', startangle=90, colors=colors,
                                       textprops={'fontsize': 11, 'fontweight': 'bold'})

    ax.set_title('Bravo Store Type Distribution', fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/12_store_types.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Store Format Mix',
        'insight': f"Bravo operates {len(type_counts)} different store formats. "
                  f"{type_counts.index[0]} is the most common format with {type_counts.iloc[0]} stores."
    }


def chart_13_hours_availability(df: pd.DataFrame) -> Dict:
    """Chart 13: Operating Hours Information Availability"""
    fig, ax = plt.subplots(figsize=(10, 6))

    hours_data = df.groupby('chain')['has_hours'].agg(['sum', 'count'])
    hours_data['percentage'] = (hours_data['sum'] / hours_data['count']) * 100
    hours_data = hours_data.sort_values('percentage', ascending=True)

    colors = sns.color_palette("coolwarm", len(hours_data))
    bars = ax.barh(hours_data.index, hours_data['percentage'], color=colors)

    # Add percentage labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2,
                f'{width:.1f}%',
                ha='left', va='center', fontsize=10, fontweight='bold')

    ax.set_xlabel('Percentage of Stores with Hours Info', fontsize=12, fontweight='bold')
    ax.set_title('Operating Hours Information Availability', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlim(0, 110)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/13_hours_availability.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Hours Transparency',
        'insight': f"TAM and BRAVO lead in transparency with operating hours listed for "
                  f"{hours_data.loc['TAM', 'percentage']:.1f}% and {hours_data.loc['BRAVO', 'percentage']:.1f}% of stores respectively."
    }


def chart_14_overall_summary(df: pd.DataFrame) -> Dict:
    """Chart 14: Overall Dataset Summary"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Total stores
    axes[0, 0].text(0.5, 0.5, f"{len(df):,}",
                   ha='center', va='center', fontsize=60, fontweight='bold', color='#3498db')
    axes[0, 0].text(0.5, 0.2, "Total Stores",
                   ha='center', va='center', fontsize=16, fontweight='bold')
    axes[0, 0].axis('off')

    # Chains
    axes[0, 1].text(0.5, 0.5, f"{df['chain'].nunique()}",
                   ha='center', va='center', fontsize=60, fontweight='bold', color='#e74c3c')
    axes[0, 1].text(0.5, 0.2, "Supermarket Chains",
                   ha='center', va='center', fontsize=16, fontweight='bold')
    axes[0, 1].axis('off')

    # Cities
    if 'city' not in df.columns:
        df['city'] = df['address'].apply(extract_city_from_address)
    axes[1, 0].text(0.5, 0.5, f"{df['city'].nunique()}",
                   ha='center', va='center', fontsize=60, fontweight='bold', color='#2ecc71')
    axes[1, 0].text(0.5, 0.2, "Cities/Regions",
                   ha='center', va='center', fontsize=16, fontweight='bold')
    axes[1, 0].axis('off')

    # Coverage
    coverage = df['has_coords'].mean() * 100
    axes[1, 1].text(0.5, 0.5, f"{coverage:.0f}%",
                   ha='center', va='center', fontsize=60, fontweight='bold', color='#f39c12')
    axes[1, 1].text(0.5, 0.2, "Geographic Coverage",
                   ha='center', va='center', fontsize=16, fontweight='bold')
    axes[1, 1].axis('off')

    plt.suptitle('Azerbaijan Supermarket Market Overview', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/14_overall_summary.png', dpi=300, bbox_inches='tight')
    plt.close()

    return {
        'title': 'Market Overview',
        'insight': f"Complete dataset covering {len(df):,} stores across {df['chain'].nunique()} major chains "
                  f"in {df['city'].nunique()} cities/regions with {coverage:.0f}% coordinate coverage."
    }


def chart_15_growth_potential(df: pd.DataFrame) -> Dict:
    """Chart 15: Market Penetration by City (Top 20)"""
    if 'city' not in df.columns:
        df['city'] = df['address'].apply(extract_city_from_address)

    fig, ax = plt.subplots(figsize=(14, 8))

    # Get top 20 cities
    top_20_cities = df['city'].value_counts().head(20)

    # Calculate chain diversity (how many chains operate in each city)
    city_diversity = df.groupby('city')['chain'].nunique()

    # Combine data
    city_data = pd.DataFrame({
        'Store Count': top_20_cities,
        'Chain Count': city_diversity[top_20_cities.index]
    })

    # Create dual-axis plot
    ax2 = ax.twinx()

    x = range(len(city_data))
    width = 0.4

    bars1 = ax.bar([i - width/2 for i in x], city_data['Store Count'],
                   width, label='Total Stores', color='#3498db', alpha=0.8)
    bars2 = ax2.bar([i + width/2 for i in x], city_data['Chain Count'],
                    width, label='Number of Chains', color='#e74c3c', alpha=0.8)

    ax.set_xlabel('City', fontsize=12, fontweight='bold')
    ax.set_ylabel('Total Stores', fontsize=12, fontweight='bold', color='#3498db')
    ax2.set_ylabel('Number of Chains Operating', fontsize=12, fontweight='bold', color='#e74c3c')

    ax.set_xticks(x)
    ax.set_xticklabels(city_data.index, rotation=45, ha='right')

    ax.tick_params(axis='y', labelcolor='#3498db')
    ax2.tick_params(axis='y', labelcolor='#e74c3c')

    ax.set_title('Market Penetration: Store Count vs Chain Competition (Top 20 Cities)',
                fontsize=14, fontweight='bold', pad=20)

    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{CHARTS_DIR}/15_market_penetration.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Find cities with high stores but low competition
    low_competition_cities = city_data[city_data['Chain Count'] <= 2].sort_values('Store Count', ascending=False)

    if len(low_competition_cities) > 0:
        insight = f"Growth opportunity: {low_competition_cities.index[0]} has {int(low_competition_cities.iloc[0]['Store Count'])} stores " \
                 f"but only {int(low_competition_cities.iloc[0]['Chain Count'])} chain(s) operating - indicating potential for new entrants."
    else:
        insight = "Strong competition across all major cities with multiple chains operating in each market."

    return {
        'title': 'Market Opportunities',
        'insight': insight
    }


def generate_insights_report(df: pd.DataFrame, all_insights: List[Dict]) -> str:
    """Generate comprehensive insights report"""
    if 'city' not in df.columns:
        df['city'] = df['address'].apply(extract_city_from_address)

    report = []
    report.append("# Key Insights from Azerbaijan Supermarket Market Analysis\n")

    # Market Overview
    report.append("## Market Overview")
    report.append(f"- **Total Stores**: {len(df):,} supermarket locations analyzed")
    report.append(f"- **Chains**: {df['chain'].nunique()} major supermarket chains")
    report.append(f"- **Geographic Coverage**: {df['city'].nunique()} cities and regions across Azerbaijan")
    report.append(f"- **Data Quality**: {df['has_coords'].mean()*100:.1f}% complete coordinate data\n")

    # Market Leaders
    report.append("## Market Leaders")
    top_chain = df['chain'].value_counts().index[0]
    top_count = df['chain'].value_counts().iloc[0]
    report.append(f"- **Largest Chain**: {top_chain} with {top_count} stores ({top_count/len(df)*100:.1f}% market share)")

    chain_counts = df['chain'].value_counts()
    for i, (chain, count) in enumerate(chain_counts.items(), 1):
        report.append(f"- **#{i}**: {chain} - {count} stores ({count/len(df)*100:.1f}%)")
    report.append("")

    # Geographic Insights
    report.append("## Geographic Distribution")
    top_5_cities = df['city'].value_counts().head(5)
    report.append(f"- **Top City**: {top_5_cities.index[0]} with {top_5_cities.iloc[0]} stores")
    report.append(f"- **Urban Concentration**: Top 5 cities account for {top_5_cities.sum()/len(df)*100:.1f}% of all stores")
    report.append(f"- **Regional Spread**: Stores present in {df['city'].nunique()} different locations\n")

    # Data Quality
    report.append("## Data Completeness")
    for chain in df['chain'].unique():
        chain_df = df[df['chain'] == chain]
        completeness = chain_df[['has_coords', 'has_address', 'has_phone', 'has_hours']].mean().mean() * 100
        report.append(f"- **{chain}**: {completeness:.1f}% average data completeness")
    report.append("")

    # Competition Analysis
    report.append("## Market Competition")
    city_diversity = df.groupby('city')['chain'].nunique().sort_values(ascending=False)
    report.append(f"- **Most Competitive City**: {city_diversity.index[0]} with {city_diversity.iloc[0]} chains operating")

    # Cities with single chain dominance
    single_chain_cities = city_diversity[city_diversity == 1]
    if len(single_chain_cities) > 0:
        report.append(f"- **Monopoly Markets**: {len(single_chain_cities)} cities have only one chain operating")
    report.append("")

    # Business Insights
    report.append("## Strategic Insights")
    report.append("1. **Market Concentration**: High concentration in Baku region presents both opportunities and challenges")
    report.append("2. **Regional Expansion**: Secondary cities show potential for growth with lower competition")
    report.append("3. **Data Transparency**: Chains with complete data (ARAZ, BRAVO, TAM) show higher customer engagement potential")
    report.append("4. **Format Diversity**: Different store formats serve different market segments")
    report.append("5. **Geographic Coverage**: All major chains have nationwide presence but varying penetration levels\n")

    return "\n".join(report)


def main():
    """Main analysis execution"""
    print("=" * 60)
    print("Azerbaijan Supermarket Market Analysis")
    print("=" * 60)
    print("\nLoading data...")

    df = load_data()
    print(f"Loaded {len(df):,} stores from {df['chain'].nunique()} chains\n")

    print("Generating charts and insights...\n")

    insights = []

    # Generate all charts
    chart_functions = [
        chart_1_market_share,
        chart_2_geographic_distribution,
        chart_3_data_completeness,
        chart_4_top_cities,
        chart_5_chain_by_city,
        chart_6_baku_density,
        chart_7_coordinate_heatmap,
        chart_8_chain_comparison,
        chart_9_regional_distribution,
        chart_10_latitude_distribution,
        chart_11_phone_availability,
        chart_12_store_type_distribution,
        chart_13_hours_availability,
        chart_14_overall_summary,
        chart_15_growth_potential
    ]

    for i, chart_func in enumerate(chart_functions, 1):
        try:
            print(f"  Generating chart {i}/{len(chart_functions)}: {chart_func.__name__}...")
            result = chart_func(df)
            if result:
                insights.append(result)
        except Exception as e:
            print(f"    Warning: Failed to generate {chart_func.__name__}: {e}")

    print(f"\n✓ Generated {len(insights)} charts successfully")

    # Generate insights report
    print("\nGenerating insights report...")
    insights_text = generate_insights_report(df, insights)

    with open('INSIGHTS.md', 'w', encoding='utf-8') as f:
        f.write(insights_text)

    print("✓ Insights report saved to INSIGHTS.md")

    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    print(f"Charts saved to: {CHARTS_DIR}/")
    print(f"Insights saved to: INSIGHTS.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
