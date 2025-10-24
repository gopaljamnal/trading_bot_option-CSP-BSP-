"""
Simplified Options Trading Bot for Dow Jones Stocks
CSP & Bull Put Spread Strategy with Strict Criteria
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yfinance as yf
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION - Easy to modify
# =============================================================================

# Dow Jones 30 Component Stocks
DOW_JONES_TICKERS = [
    'AAPL', 'MSFT', 'JPM', 'V', 'UNH', 'HD', 'PG', 'JNJ', 'CVX', 'MRK',
    'DIS', 'CSCO', 'CRM', 'NKE', 'KO', 'MCD', 'WMT', 'IBM', 'CAT', 'GS',
    'TRV', 'AXP', 'BA', 'MMM', 'AMGN', 'HON', 'VZ', 'DOW', 'INTC', 'WBA'
]

top50_sp500_tickers = [
    "NVDA",  # Nvidia :contentReference[oaicite:1]{index=1}
    "MSFT",  # Microsoft :contentReference[oaicite:2]{index=2}
    "AAPL",  # Apple Inc. :contentReference[oaicite:3]{index=3}
    "AMZN",  # Amazon.com :contentReference[oaicite:4]{index=4}
    "META",  # Meta Platforms :contentReference[oaicite:5]{index=5}
    "AVGO",  # Broadcom :contentReference[oaicite:6]{index=6}
    "GOOGL", # Alphabet Class A :contentReference[oaicite:7]{index=7}
    "GOOG",  # Alphabet Class C :contentReference[oaicite:8]{index=8}
    "TSLA",  # Tesla :contentReference[oaicite:9]{index=9}
    "BRK.B", # Berkshire Hathaway Class B :contentReference[oaicite:10]{index=10}
    "WMT",   # Walmart :contentReference[oaicite:11]{index=11}
    "ORCL",  # Oracle Corporation :contentReference[oaicite:12]{index=12}
    "JPM",   # JPMorgan Chase :contentReference[oaicite:13]{index=13}
    "LLY",   # Eli Lilly :contentReference[oaicite:14]{index=14}
    "V",     # Visa Inc. :contentReference[oaicite:15]{index=15}
    "NFLX",  # Netflix :contentReference[oaicite:16]{index=16}
    "MA",    # Mastercard :contentReference[oaicite:17]{index=17}
    "XOM",   # ExxonMobil :contentReference[oaicite:18]{index=18}
    "JNJ",   # Johnson & Johnson :contentReference[oaicite:19]{index=19}
    "PLTR",  # Palantir Technologies :contentReference[oaicite:20]{index=20}
    "COST",  # Costco Wholesale :contentReference[oaicite:21]{index=21}
    "ABBV",  # AbbVie :contentReference[oaicite:22]{index=22}
    "HD",    # Home Depot :contentReference[oaicite:23]{index=23}
    "AMD",   # Advanced Micro Devices :contentReference[oaicite:24]{index=24}
    "BAC",   # Bank of America :contentReference[oaicite:25]{index=25}
    "PG",    # Procter & Gamble :contentReference[oaicite:26]{index=26}
    "UNH",   # UnitedHealth Group :contentReference[oaicite:27]{index=27}
    "CVX",   # Chevron Corporation — more recent data suggests top-50; weight mentioned in sources. :contentReference[oaicite:28]{index=28}
    "PFE",   # Pfizer Inc. — often appears in top 30-50 by weight. :contentReference[oaicite:29]{index=29}
    "DIS",   # The Walt Disney Company — common in top lists of large cap. (weight approx)
    "KO",    # Coca-Cola Company — large-cap staple, often in top 50.
    "CSCO",  # Cisco Systems — large tech/communications hardware.
    "MCD",   # McDonalds Corporation — large consumer company.
    "INTC",  # Intel Corporation — large cap semiconductor.
    "NVAX",  # (example, though maybe slightly outside top 50)
    "T",     # AT&T Inc. — large telco (historically in big indices)
    "PEP",   # PepsiCo Inc.
    "WBA",   # Walgreens Boots Alliance Inc.
    "MMM",   # 3M Company — large industrial cap stock.
    "GE",    # General Electric Company — large in industrials.
    "BMY",   # Bristol-Myers Squibb — large pharmaceutical.
    "MDT",   # Medtronic plc — large medical devices company.
    "C",     # Citigroup Inc. — big bank, often among large cap.
    "GS",    # Goldman Sachs Group Inc. — major financial institution.
    "AXP",   # American Express Company — large financial/consumer.
    "NEE",   # NextEra Energy Inc. — large utility/electric company.
    "TMO",   # Thermo Fisher Scientific Inc. — large life sciences tools/solutions.
    "RTX",   # RTX Corporation (formerly Raytheon Technologies) — large aerospace/defense.
    "LMT",   # Lockheed Martin Corporation — large defense contractor.
    "AMGN",  # Amgen Inc. — large biotech.
    "UNP",   # Union Pacific Corporation — large rail/transportation.
    "SOFI", "HIMS", "SBUX", "HOODS"
]



# Screening Criteria
MIN_DTE = 1               # Minimum days to expiration
MAX_DTE = 7             # Maximum days to expiration
MIN_OTM_PERCENT = 5      # Minimum 10% out of the money
MAX_OTM_PERCENT = 10      # Maximum 15% out of the money
SPREAD_WIDTH = 5.00       # Exactly $5 spread width ($500 per contract)
MIN_RETURN_ON_RISK = 20   # Minimum 20% return on risk
MIN_VOLUME = 10           # Minimum option volume
MIN_OPEN_INTEREST = 50    # Minimum open interest

# =============================================================================
# DATABASE MANAGER
# =============================================================================

class DatabaseManager:
    """Simple SQLite database for trade logging"""

    def __init__(self, db_path='options_trades.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create trades table if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                symbol TEXT,
                strategy TEXT,
                short_strike REAL,
                long_strike REAL,
                credit REAL,
                max_risk REAL,
                return_pct REAL,
                expiry TEXT,
                dte INTEGER,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def save_trade(self, trade_data: Dict):
        """Save trade to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trades (date, symbol, strategy, short_strike, long_strike,
                              credit, max_risk, return_pct, expiry, dte, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            trade_data['symbol'],
            trade_data['strategy'],
            trade_data['short_strike'],
            trade_data.get('long_strike'),
            trade_data['credit'],
            trade_data['max_risk'],
            trade_data['return_on_risk'],
            trade_data['expiry'],
            trade_data['dte'],
            'open'
        ))
        conn.commit()
        conn.close()

    def get_all_trades(self) -> pd.DataFrame:
        """Get all trades as DataFrame"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades", conn)
        conn.close()
        return df

# =============================================================================
# OPTIONS SCREENER
# =============================================================================

class OptionsScreener:
    """Simple options screener for Dow Jones stocks"""

    def __init__(self, tickers: List[str]):
        self.tickers = tickers

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')
            if not data.empty:
                return float(data['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
        return None

    def get_options_chain(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get options chain for valid expirations"""
        try:
            ticker = yf.Ticker(symbol)
            expirations = ticker.options

            if not expirations:
                return None

            all_puts = []
            current_date = datetime.now()

            for exp_str in expirations:
                exp_date = datetime.strptime(exp_str, '%Y-%m-%d')
                dte = (exp_date - current_date).days

                # Filter by DTE range
                if MIN_DTE <= dte <= MAX_DTE:
                    chain = ticker.option_chain(exp_str)
                    puts = chain.puts.copy()
                    puts['expiry'] = exp_date
                    puts['expiry_str'] = exp_str
                    puts['dte'] = dte
                    all_puts.append(puts)

            if all_puts:
                return pd.concat(all_puts, ignore_index=True)

        except Exception as e:
            logger.error(f"Error fetching options for {symbol}: {e}")

        return None

    def screen_csp(self, symbol: str) -> List[Dict]:
        """Screen for Cash Secured Puts"""
        candidates = []

        # Get current price
        current_price = self.get_current_price(symbol)
        if not current_price:
            return candidates

        # Get options chain
        chain = self.get_options_chain(symbol)
        if chain is None or len(chain) == 0:
            return candidates

        # Calculate target strike range
        min_strike = current_price * (1 - MAX_OTM_PERCENT / 100)
        max_strike = current_price * (1 - MIN_OTM_PERCENT / 100)

        # Filter chain
        chain = chain[
            (chain['strike'] >= min_strike) &
            (chain['strike'] <= max_strike) &
            (chain['volume'] >= MIN_VOLUME) &
            (chain['openInterest'] >= MIN_OPEN_INTEREST) &
            (chain['bid'] > 0) &
            (chain['ask'] > 0)
        ]

        # Process each option
        for _, row in chain.iterrows():
            strike = float(row['strike'])
            bid = float(row['bid'])
            ask = float(row['ask'])
            premium = (bid + ask) / 2

            # Calculate metrics
            otm_percent = ((current_price - strike) / current_price) * 100
            return_on_risk = (premium / strike) * 100
            max_risk = strike * 100  # Per contract

            # Check criteria
            if return_on_risk >= MIN_RETURN_ON_RISK:
                dte = int(row['dte'])
                annualized_return = return_on_risk * (365 / dte)

                candidates.append({
                    'symbol': symbol,
                    'strategy': 'CSP',
                    'current_price': current_price,
                    'strike': strike,
                    'short_strike': strike,
                    'long_strike': None,
                    'premium': premium,
                    'bid': bid,
                    'ask': ask,
                    'credit': premium,
                    'max_risk': max_risk,
                    'otm_percent': otm_percent,
                    'return_on_risk': return_on_risk,
                    'annualized_return': annualized_return,
                    'expiry': row['expiry'],
                    'expiry_str': row['expiry_str'],
                    'dte': dte,
                    'volume': int(row['volume']),
                    'open_interest': int(row['openInterest'])
                })

        return candidates

    def screen_bull_put_spread(self, symbol: str) -> List[Dict]:
        """Screen for Bull Put Spreads with exact $5 width"""
        candidates = []

        # Get current price
        current_price = self.get_current_price(symbol)
        if not current_price:
            return candidates

        # Get options chain
        chain = self.get_options_chain(symbol)
        if chain is None or len(chain) == 0:
            return candidates

        # Calculate target strike range
        min_strike = current_price * (1 - MAX_OTM_PERCENT / 100)
        max_strike = current_price * (1 - MIN_OTM_PERCENT / 100)

        # Filter chain
        chain = chain[
            (chain['strike'] >= min_strike - SPREAD_WIDTH) &
            (chain['strike'] <= max_strike) &
            (chain['volume'] >= MIN_VOLUME / 2) &  # Relaxed for spreads
            (chain['openInterest'] >= MIN_OPEN_INTEREST / 2) &
            (chain['bid'] > 0) &
            (chain['ask'] > 0)
        ]

        # Group by expiration
        for expiry in chain['expiry'].unique():
            expiry_chain = chain[chain['expiry'] == expiry].copy()
            expiry_chain = expiry_chain.sort_values('strike', ascending=False)

            # Find spread pairs with exactly $5 width
            for _, short_row in expiry_chain.iterrows():
                short_strike = float(short_row['strike'])

                # Skip if short strike not in target range
                if short_strike < min_strike or short_strike > max_strike:
                    continue

                # Look for long strike exactly $5 below
                long_strike = short_strike - SPREAD_WIDTH

                long_options = expiry_chain[
                    (expiry_chain['strike'] >= long_strike - 0.50) &
                    (expiry_chain['strike'] <= long_strike + 0.50)
                ]

                if len(long_options) == 0:
                    continue

                # Use closest strike to target
                long_row = long_options.iloc[0]
                actual_long_strike = float(long_row['strike'])

                # Calculate spread metrics
                short_premium = (float(short_row['bid']) + float(short_row['ask'])) / 2
                long_premium = (float(long_row['bid']) + float(long_row['ask'])) / 2
                net_credit = short_premium - long_premium

                actual_width = short_strike - actual_long_strike
                max_risk = (actual_width - net_credit) * 100  # Per contract

                if max_risk <= 0 or net_credit <= 0:
                    continue

                return_on_risk = (net_credit / actual_width) * 100

                # Check criteria
                if return_on_risk >= MIN_RETURN_ON_RISK:
                    otm_percent = ((current_price - short_strike) / current_price) * 100
                    dte = int(short_row['dte'])
                    annualized_return = return_on_risk * (365 / dte)

                    candidates.append({
                        'symbol': symbol,
                        'strategy': 'BPS',
                        'current_price': current_price,
                        'short_strike': short_strike,
                        'long_strike': actual_long_strike,
                        'short_premium': short_premium,
                        'long_premium': long_premium,
                        'credit': net_credit,
                        'spread_width': actual_width,
                        'max_risk': max_risk,
                        'otm_percent': otm_percent,
                        'return_on_risk': return_on_risk,
                        'annualized_return': annualized_return,
                        'expiry': short_row['expiry'],
                        'expiry_str': short_row['expiry_str'],
                        'dte': dte,
                        'short_volume': int(short_row['volume']),
                        'long_volume': int(long_row['volume'])
                    })

        return candidates

    def screen_all_stocks(self) -> Dict[str, List[Dict]]:
        """Screen all Dow Jones stocks"""
        results = {'CSP': [], 'BPS': []}

        logger.info(f"\n{'='*80}")
        logger.info(f"Screening {len(self.tickers)} Dow Jones Stocks")
        logger.info(f"DTE Range: {MIN_DTE}-{MAX_DTE} days | OTM: {MIN_OTM_PERCENT}-{MAX_OTM_PERCENT}%")
        logger.info(f"Spread Width: ${SPREAD_WIDTH} | Min ROR: {MIN_RETURN_ON_RISK}%")
        logger.info(f"{'='*80}\n")

        for i, symbol in enumerate(self.tickers, 1):
            logger.info(f"[{i}/{len(self.tickers)}] Screening {symbol}...")

            try:
                # Screen CSP
                csp_results = self.screen_csp(symbol)
                results['CSP'].extend(csp_results)

                # Screen BPS
                bps_results = self.screen_bull_put_spread(symbol)
                results['BPS'].extend(bps_results)

                logger.info(f"  Found: {len(csp_results)} CSP, {len(bps_results)} BPS")

            except Exception as e:
                logger.error(f"  Error screening {symbol}: {e}")
                continue

        # Sort by annualized return
        results['CSP'].sort(key=lambda x: x['annualized_return'], reverse=True)
        results['BPS'].sort(key=lambda x: x['annualized_return'], reverse=True)

        return results

# =============================================================================
# DISPLAY RESULTS
# =============================================================================

def display_results(results: Dict[str, List[Dict]]):
    """Display screening results in formatted tables"""

    csp_candidates = results['CSP']
    bps_candidates = results['BPS']

    # CSP Results
    print("\n" + "="*100)
    print("CASH SECURED PUT (CSP) OPPORTUNITIES")
    print("="*100)
    print(f"Total Candidates Found: {len(csp_candidates)}\n")

    if csp_candidates:
        print("Top 15 CSP Trades:")
        print("-"*100)
        for i, trade in enumerate(csp_candidates[:15], 1):
            print(f"\n{i:2d}. {trade['symbol']:5s} | Current: ${trade['current_price']:7.2f} | Strike: ${trade['strike']:7.2f} ({trade['otm_percent']:.1f}% OTM)")
            print(f"    Premium: ${trade['premium']:.2f} | Max Risk: ${trade['max_risk']:,.0f}")
            print(f"    Return on Risk: {trade['return_on_risk']:.1f}% | Annualized: {trade['annualized_return']:.0f}%")
            print(f"    Expiry: {trade['expiry_str']} ({trade['dte']} DTE) | Vol: {trade['volume']} | OI: {trade['open_interest']}")
    else:
        print("No CSP candidates found matching criteria")

    # BPS Results
    print("\n\n" + "="*100)
    print("BULL PUT SPREAD (BPS) OPPORTUNITIES")
    print("="*100)
    print(f"Total Candidates Found: {len(bps_candidates)}\n")

    if bps_candidates:
        print("Top 15 BPS Trades:")
        print("-"*100)
        for i, trade in enumerate(bps_candidates[:15], 1):
            print(f"\n{i:2d}. {trade['symbol']:5s} | Current: ${trade['current_price']:7.2f} | Spread: ${trade['short_strike']:.2f}/${trade['long_strike']:.2f}")
            print(f"    Width: ${trade['spread_width']:.2f} | Credit: ${trade['credit']:.2f} | Max Risk: ${trade['max_risk']:,.0f}")
            print(f"    Return on Risk: {trade['return_on_risk']:.1f}% | Annualized: {trade['annualized_return']:.0f}%")
            print(f"    Expiry: {trade['expiry_str']} ({trade['dte']} DTE) | {trade['otm_percent']:.1f}% OTM")
    else:
        print("No BPS candidates found matching criteria")

    # Summary
    print("\n\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print(f"Total CSP Opportunities: {len(csp_candidates)}")
    print(f"Total BPS Opportunities: {len(bps_candidates)}")

    if csp_candidates:
        avg_csp_return = sum(t['return_on_risk'] for t in csp_candidates) / len(csp_candidates)
        print(f"Average CSP Return on Risk: {avg_csp_return:.1f}%")

    if bps_candidates:
        avg_bps_return = sum(t['return_on_risk'] for t in bps_candidates) / len(bps_candidates)
        print(f"Average BPS Return on Risk: {avg_bps_return:.1f}%")

    print("="*100)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function"""

    # Initialize screener with Dow Jones stocks
    screener = OptionsScreener(top50_sp500_tickers)

    # Run screening
    results = screener.screen_all_stocks()

    # Display results
    display_results(results)

    # Optional: Save to database
    db = DatabaseManager()

    print("\n\nWould you like to save these trades to database? (Not automated - for manual review)")

if __name__ == "__main__":
    main()
