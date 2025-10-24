"""
Daily Options Trading Checklist & News Analyzer
Simple, easy-to-modify script with comprehensive market analysis
"""


#pip install textblob
#python -m textblob.download_corpora

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from textblob import TextBlob  # Simple sentiment analysis (pip install textblob)
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION - EASY TO MODIFY
# =============================================================================

# Your Watchlist (Dow Jones 30 by default)
WATCHLIST = [
    'AAPL', 'MSFT', 'JPM', 'V', 'UNH', 'HD', 'PG', 'JNJ', 'CVX', 'MRK',
    'DIS', 'CSCO', 'CRM', 'NKE', 'KO', 'MCD', 'WMT', 'IBM', 'CAT', 'GS',
    'TRV', 'AXP', 'BA', 'MMM', 'AMGN', 'HON', 'VZ', 'DOW', 'INTC', 'WBA'
]

# Key Market Indices to Monitor
MARKET_INDICES = {
    '^GSPC': 'S&P 500',
    '^IXIC': 'NASDAQ',
    '^DJI': 'Dow Jones',
    '^VIX': 'VIX (Volatility)'
}

# News Categories (for classification)
NEWS_KEYWORDS = {
    'EARNINGS': ['earnings', 'revenue', 'profit', 'eps', 'guidance', 'beat', 'miss', 'quarterly'],
    'UPGRADE/DOWNGRADE': ['upgrade', 'downgrade', 'rating', 'price target', 'analyst', 'overweight', 'underweight'],
    'REGULATORY': ['fda', 'sec', 'lawsuit', 'investigation', 'fine', 'regulation', 'approval'],
    'GEOPOLITICAL': ['tariff', 'china', 'trade war', 'sanctions', 'russia', 'conflict'],
    'ECONOMIC': ['fed', 'inflation', 'interest rate', 'recession', 'gdp', 'jobs', 'unemployment'],
    'CORPORATE': ['merger', 'acquisition', 'ceo', 'layoff', 'restructure', 'deal', 'partnership'],
    'PRODUCT': ['launch', 'recall', 'innovation', 'patent', 'new product']
}

# =============================================================================
# MARKET DATA FUNCTIONS
# =============================================================================

def get_market_overview() -> Dict:
    """Get current market conditions (Step 1: Macro & Market Overview)"""
    logger.info("📊 Fetching market overview...")
    
    market_data = {}
    
    for symbol, name in MARKET_INDICES.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d')
            
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                change = ((current - prev) / prev) * 100
                
                market_data[name] = {
                    'price': current,
                    'change': change,
                    'trend': '📈 UP' if change > 0 else '📉 DOWN' if change < 0 else '➡️ FLAT'
                }
        except Exception as e:
            logger.error(f"Error fetching {name}: {e}")
    
    return market_data

def check_vix() -> Dict:
    """Check VIX volatility level"""
    try:
        vix = yf.Ticker('^VIX')
        hist = vix.history(period='5d')
        
        if not hist.empty:
            current_vix = hist['Close'].iloc[-1]
            prev_vix = hist['Close'].iloc[-2] if len(hist) > 1 else current_vix
            
            # VIX interpretation
            if current_vix < 15:
                level = 'LOW (Complacent)'
                risk = '✅ Low volatility - Good for selling premium'
            elif current_vix < 20:
                level = 'NORMAL'
                risk = '✅ Normal conditions - Standard strategies OK'
            elif current_vix < 30:
                level = 'ELEVATED'
                risk = '⚠️ Higher volatility - Use caution'
            else:
                level = 'HIGH (Fear)'
                risk = '🚨 High volatility - Avoid selling puts or use wider strikes'
            
            return {
                'current': current_vix,
                'previous': prev_vix,
                'level': level,
                'risk_assessment': risk,
                'rising': current_vix > prev_vix
            }
    except Exception as e:
        logger.error(f"Error fetching VIX: {e}")
    
    return {'current': 0, 'level': 'UNKNOWN', 'risk_assessment': 'Unable to fetch VIX data'}

def get_economic_calendar() -> str:
    """Check for major economic events today (Step 2: Economic Data)"""
    # Note: For full calendar, use APIs like https://www.alphavantage.co or tradingeconomics
    today = datetime.now()
    day_name = today.strftime('%A')
    
    # Common economic release days
    economic_events = []
    
    if day_name == 'Friday':
        economic_events.append('Check for: Jobs Report (first Friday of month)')
    if today.day <= 7 and day_name == 'Friday':
        economic_events.append('⚠️ LIKELY: Monthly Jobs Report')
    if today.day >= 10 and today.day <= 15:
        economic_events.append('Check for: CPI/PPI Inflation Data (mid-month)')
    
    # FOMC meetings (typically 8x per year)
    fomc_message = "Check FOMC calendar for interest rate decisions"
    
    if economic_events:
        return '\n   • '.join([''] + economic_events + [fomc_message])
    else:
        return f"\n   • No major scheduled events for {day_name}\n   • {fomc_message}"

# =============================================================================
# NEWS & SENTIMENT FUNCTIONS
# =============================================================================

def analyze_sentiment_textblob(text: str) -> Dict:
    """Analyze sentiment using TextBlob (simple and reliable)"""
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 (negative) to 1 (positive)
        
        if polarity > 0.1:
            label = 'POSITIVE'
            emoji = '🟢'
        elif polarity < -0.1:
            label = 'NEGATIVE'
            emoji = '🔴'
        else:
            label = 'NEUTRAL'
            emoji = '⚪'
        
        return {
            'score': polarity,
            'label': label,
            'emoji': emoji
        }
    except:
        return {'score': 0, 'label': 'NEUTRAL', 'emoji': '⚪'}

def categorize_news(title: str) -> List[str]:
    """Categorize news by keywords"""
    title_lower = title.lower()
    categories = []
    
    for category, keywords in NEWS_KEYWORDS.items():
        if any(keyword in title_lower for keyword in keywords):
            categories.append(category)
    
    return categories if categories else ['GENERAL']

def fetch_stock_news(symbol: str, max_articles: int = 5) -> List[Dict]:
    """Fetch news for a specific stock"""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        
        if not news:
            return []
        
        processed_news = []
        for article in news[:max_articles]:
            title = article.get('title', '')
            published = datetime.fromtimestamp(article.get('providerPublishTime', 0))
            days_ago = (datetime.now() - published).days
            
            # Sentiment analysis
            sentiment = analyze_sentiment_textblob(title)
            
            # Categorize
            categories = categorize_news(title)
            
            processed_news.append({
                'symbol': symbol,
                'title': title,
                'publisher': article.get('publisher', 'Unknown'),
                'link': article.get('link', ''),
                'published': published,
                'days_ago': days_ago,
                'sentiment': sentiment,
                'categories': categories
            })
        
        return processed_news
    
    except Exception as e:
        logger.error(f"Error fetching news for {symbol}: {e}")
        return []

def get_stock_technicals(symbol: str) -> Dict:
    """Get technical levels for a stock (Step 4: Technical Setup)"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='30d')
        
        if hist.empty:
            return {}
        
        current_price = hist['Close'].iloc[-1]
        high_30d = hist['High'].max()
        low_30d = hist['Low'].min()
        
        # Calculate support/resistance (simple method)
        support = low_30d
        resistance = high_30d
        
        # IV Rank (simplified - would need historical IV data for accurate calculation)
        info = ticker.info
        iv_estimate = info.get('impliedVolatility', 0) if info.get('impliedVolatility') else 'N/A'
        
        return {
            'current_price': current_price,
            'support': support,
            'resistance': resistance,
            'iv': iv_estimate,
            'distance_from_low': ((current_price - low_30d) / low_30d) * 100,
            'distance_from_high': ((high_30d - current_price) / high_30d) * 100
        }
    
    except Exception as e:
        logger.error(f"Error getting technicals for {symbol}: {e}")
        return {}

def check_earnings_calendar(symbol: str) -> Optional[str]:
    """Check if earnings are coming up"""
    try:
        ticker = yf.Ticker(symbol)
        calendar = ticker.calendar
        
        if calendar is not None and not calendar.empty:
            # Try to get earnings date
            if 'Earnings Date' in calendar.index:
                earnings_date = calendar.loc['Earnings Date'].values[0]
                
                if isinstance(earnings_date, pd.Timestamp):
                    days_until = (earnings_date - pd.Timestamp.now()).days
                    
                    if 0 <= days_until <= 7:
                        return f"⚠️ EARNINGS IN {days_until} DAYS"
        
        return None
    except:
        return None

# =============================================================================
# CHECKLIST GENERATOR
# =============================================================================

def generate_daily_checklist() -> str:
    """Generate formatted daily checklist report"""
    
    report = []
    report.append("\n" + "="*100)
    report.append("📋 DAILY OPTIONS TRADING CHECKLIST")
    report.append("="*100)
    report.append(f"Date: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p ET')}")
    report.append("="*100)
    
    # =========================================================================
    # STEP 1: MACRO & MARKET OVERVIEW (Before 8:30 AM ET)
    # =========================================================================
    
    report.append("\n" + "🌍 STEP 1: MACRO & MARKET OVERVIEW (Before 8:30 AM ET)")
    report.append("-"*100)
    
    market_data = get_market_overview()
    vix_data = check_vix()
    
    report.append("\n📊 Market Indices:")
    for name, data in market_data.items():
        report.append(f"   • {name}: {data['price']:.2f} ({data['change']:+.2f}%) {data['trend']}")
    
    report.append(f"\n📈 VIX Volatility Index:")
    report.append(f"   • Current: {vix_data['current']:.2f} - {vix_data['level']}")
    report.append(f"   • Assessment: {vix_data['risk_assessment']}")
    if vix_data.get('rising'):
        report.append("   • ⚠️ VIX is RISING - Exercise caution with new positions")
    
    report.append("\n✅ Why It Matters:")
    report.append("   Tells you if the day is risk-on or risk-off — avoid selling puts when volatility spikes")
    
    # =========================================================================
    # STEP 2: ECONOMIC DATA RELEASE CHECK (8:30 AM ET)
    # =========================================================================
    
    report.append("\n\n" + "📅 STEP 2: ECONOMIC DATA RELEASE CHECK (8:30 AM ET)")
    report.append("-"*100)
    
    econ_events = get_economic_calendar()
    report.append("\n📊 Today's Economic Events:")
    report.append(econ_events)
    
    report.append("\n✅ Why It Matters:")
    report.append("   Avoid new trades right before big data drops (implied volatility risk)")
    
    # =========================================================================
    # STEP 3: NEWS SCAN (8:45-9:15 AM ET)
    # =========================================================================
    
    report.append("\n\n" + "📰 STEP 3: NEWS SCAN - STOCK & SECTOR (8:45-9:15 AM ET)")
    report.append("-"*100)
    
    report.append("\n🔍 Scanning top news for your watchlist...")
    
    # Track stocks with catalysts
    stocks_with_news = []
    negative_catalysts = []
    positive_catalysts = []
    
    for symbol in WATCHLIST[:10]:  # Scan first 10 for speed
        news_items = fetch_stock_news(symbol, max_articles=3)
        
        if news_items:
            has_significant_news = False
            
            for article in news_items:
                # Only show recent news (last 3 days)
                if article['days_ago'] <= 3:
                    has_significant_news = True
                    
                    sentiment_emoji = article['sentiment']['emoji']
                    sentiment_label = article['sentiment']['label']
                    categories_str = ', '.join(article['categories'])
                    
                    if article['sentiment']['label'] == 'NEGATIVE':
                        negative_catalysts.append({
                            'symbol': symbol,
                            'title': article['title'],
                            'categories': categories_str
                        })
                    elif article['sentiment']['label'] == 'POSITIVE':
                        positive_catalysts.append({
                            'symbol': symbol,
                            'title': article['title'],
                            'categories': categories_str
                        })
            
            if has_significant_news:
                stocks_with_news.append(symbol)
    
    # Display catalysts
    if negative_catalysts:
        report.append("\n🚨 NEGATIVE CATALYSTS (Avoid or Use Caution):")
        for item in negative_catalysts[:5]:
            report.append(f"\n   • [{item['symbol']}] {item['title']}")
            report.append(f"     Categories: {item['categories']}")
    
    if positive_catalysts:
        report.append("\n\n✅ POSITIVE CATALYSTS (Potential Opportunities):")
        for item in positive_catalysts[:5]:
            report.append(f"\n   • [{item['symbol']}] {item['title']}")
            report.append(f"     Categories: {item['categories']}")
    
    if not negative_catalysts and not positive_catalysts:
        report.append("\n   ✅ No major catalysts detected in recent news")
    
    report.append("\n\n✅ Why It Matters:")
    report.append("   Identifies sudden catalysts that can move your stock")
    
    # =========================================================================
    # STEP 4: TECHNICAL & VOLATILITY SETUP (9:15-9:25 AM ET)
    # =========================================================================
    
    report.append("\n\n" + "📊 STEP 4: TECHNICAL & VOLATILITY SETUP (9:15-9:25 AM ET)")
    report.append("-"*100)
    
    report.append("\n🎯 Key Support/Resistance Levels:")
    
    # Show technicals for stocks with news or random sample
    sample_stocks = stocks_with_news[:3] if stocks_with_news else WATCHLIST[:3]
    
    for symbol in sample_stocks:
        technicals = get_stock_technicals(symbol)
        earnings_alert = check_earnings_calendar(symbol)
        
        if technicals:
            report.append(f"\n   • {symbol}: ${technicals['current_price']:.2f}")
            report.append(f"     Support: ${technicals['support']:.2f} | Resistance: ${technicals['resistance']:.2f}")
            if earnings_alert:
                report.append(f"     {earnings_alert}")
    
    report.append("\n\n✅ Why It Matters:")
    report.append("   Ensures you sell puts below strong support with enough premium")
    
    # =========================================================================
    # STEP 5: PRO TIP ROUTINE (Takes 10-15 minutes total)
    # =========================================================================
    
    report.append("\n\n" + "✅ PRO TIP ROUTINE (10-15 minutes before trading)")
    report.append("-"*100)
    
    # Generate trading decision
    decision = generate_trading_decision(market_data, vix_data, negative_catalysts)
    
    report.append("\n1. ✅ Check Futures + VIX → " + decision['futures_check'])
    report.append("2. ✅ Check Economic Calendar → " + decision['econ_check'])
    report.append("3. ✅ Scan News for My Stocks → " + decision['news_check'])
    report.append("4. ✅ Check Technical & IV Setup → " + decision['technical_check'])
    report.append(f"5. ✅ DECISION: {decision['action']}")
    
    report.append("\n" + "="*100)
    report.append("📊 NEXT STEPS:")
    report.append("="*100)
    report.append(decision['next_steps'])
    report.append("="*100)
    
    return '\n'.join(report)

def generate_trading_decision(market_data, vix_data, negative_catalysts) -> Dict:
    """Generate trading decision based on checklist"""
    
    # Analyze market conditions
    sp500_trend = market_data.get('S&P 500', {}).get('change', 0)
    vix_level = vix_data.get('current', 20)
    
    # Decision logic
    if vix_level > 25:
        action = "⚠️ WAIT - VIX too high, volatility elevated"
        next_steps = "• Skip today or use very conservative strikes (25%+ OTM)\n• Consider waiting for VIX to settle"
    elif len(negative_catalysts) > 5:
        action = "⚠️ CAUTION - Multiple negative catalysts present"
        next_steps = "• Focus on stocks WITHOUT negative news\n• Use wider strikes and smaller position sizes"
    elif sp500_trend < -1.5:
        action = "⚠️ WAIT - Market selling off, avoid new trades"
        next_steps = "• Wait for market stabilization\n• Review existing positions only"
    else:
        action = "✅ ENTER TRADE - Market conditions favorable"
        next_steps = "• Run options screening bot\n• Select 2-3 CSP and 1 BPS from results\n• Execute trades with proper position sizing"
    
    return {
        'futures_check': f"Market {'UP' if sp500_trend > 0 else 'DOWN'} ({sp500_trend:+.2f}%), VIX at {vix_level:.1f}",
        'econ_check': "See economic calendar section above",
        'news_check': f"{len(negative_catalysts)} negative catalysts detected",
        'technical_check': "Support/resistance levels identified above",
        'action': action,
        'next_steps': next_steps
    }

# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_checklist(report: str, filename: str = None):
    """Export checklist to text file"""
    if filename is None:
        filename = f"trading_checklist_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"\n✅ Checklist exported to {filename}")

def export_news_to_csv(symbols: List[str], filename: str = None):
    """Export detailed news to CSV"""
    if filename is None:
        filename = f"news_analysis_{datetime.now().strftime('%Y%m%d')}.csv"
    
    all_news = []
    
    for symbol in symbols:
        news_items = fetch_stock_news(symbol, max_articles=10)
        for item in news_items:
            all_news.append({
                'Symbol': item['symbol'],
                'Title': item['title'],
                'Sentiment': item['sentiment']['label'],
                'Sentiment_Score': item['sentiment']['score'],
                'Categories': ', '.join(item['categories']),
                'Publisher': item['publisher'],
                'Days_Ago': item['days_ago'],
                'Published': item['published'].strftime('%Y-%m-%d %H:%M'),
                'Link': item['link']
            })
    
    if all_news:
        df = pd.DataFrame(all_news)
        df.to_csv(filename, index=False)
        logger.info(f"✅ Detailed news exported to {filename}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution - Generate daily checklist"""
    
    print("\n" + "="*100)
    print("🚀 GENERATING DAILY OPTIONS TRADING CHECKLIST")
    print("="*100)
    print("This will take 1-2 minutes to fetch all data...\n")
    
    # Generate checklist
    checklist_report = generate_daily_checklist()
    
    # Display to console
    print(checklist_report)
    
    # Export to file
    export_checklist(checklist_report)
    
    # Optional: Export detailed news to CSV
    export_news_to_csv(WATCHLIST)
    
    print("\n" + "="*100)
    print("✅ CHECKLIST COMPLETE - Ready to trade!")
    print("="*100)

if __name__ == "__main__":
    main()