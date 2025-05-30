import os
from google.adk.agents import Agent
from typing import Dict, Any, Optional
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'YOUR_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', 'YOUR_NEWS_API_KEY')

@dataclass
class StockData:
    ticker: str
    company_name: str
    current_price: Optional[float] = None
    price_change: Optional[float] = None
    percent_change: Optional[float] = None
    news: Optional[list] = None
    historical_data: Optional[dict] = None

def identify_ticker(query: str) -> Dict[str, Any]:
    """Identify stock ticker from company name in user query"""
    ticker_mapping = {
        'tesla': 'TSLA',
        'palantir': 'PLTR',
        'nvidia': 'NVDA',
        'apple': 'AAPL',
        'microsoft': 'MSFT',
        'amazon': 'AMZN',
        'google': 'GOOGL',
        'alphabet': 'GOOGL',
        'meta': 'META',
        'facebook': 'META',
        'netflix': 'NFLX',
        'amd': 'AMD',
        'intel': 'INTC',
        'walmart': 'WMT',
        'disney': 'DIS',
        'coca cola': 'KO',
        'pepsi': 'PEP',
        'boeing': 'BA',
        'ford': 'F',
        'general motors': 'GM',
        'jp morgan': 'JPM',
        'bank of america': 'BAC',
        'wells fargo': 'WFC'
    }
    
    query_lower = query.lower()
    matched_ticker = None
    company_name = None
    
    # First check direct ticker mentions
    words = query_lower.split()
    for word in words:
        if word.upper() in ['TSLA', 'PLTR', 'NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NFLX', 'AMD', 'INTC', 'WMT', 'DIS', 'KO', 'PEP', 'BA', 'F', 'GM', 'JPM', 'BAC', 'WFC']:
            matched_ticker = word.upper()
            # Find company name from reverse mapping
            for name, ticker in ticker_mapping.items():
                if ticker == matched_ticker:
                    company_name = name.title()
                    break
            if company_name is None:
                company_name = matched_ticker
            break
    
    # Then check company names
    if not matched_ticker:
        for name, ticker in ticker_mapping.items():
            if name in query_lower:
                matched_ticker = ticker
                company_name = name.title()
                break
    
    # If still not found, try Alpha Vantage search
    if not matched_ticker and ALPHA_VANTAGE_API_KEY != 'YOUR_API_KEY':
        try:
            search_terms = [word for word in query_lower.split() if word not in ['stock', 'price', 'today', 'yesterday', 'week', 'month', 'why', 'did', 'drop', 'rise', 'up', 'down', 'change']]
            search_query = ' '.join(search_terms[:3])  # Take first 3 relevant words
            
            url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={search_query}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'bestMatches' in data and len(data['bestMatches']) > 0:
                matched_ticker = data['bestMatches'][0]['1. symbol']
                company_name = data['bestMatches'][0]['2. name']
        except Exception as e:
            print(f"Error searching for ticker: {e}")
    
    if not matched_ticker:
        return {
            'status': 'error',
            'error_message': f'Could not identify stock ticker from query: "{query}". Please specify a company name or ticker symbol.'
        }
    
    return {
        'status': 'success',
        'ticker': matched_ticker,
        'company_name': company_name or matched_ticker
    }

def ticker_news(ticker: str, company_name: str) -> Dict[str, Any]:
    """Retrieve recent news about the stock"""
    if NEWS_API_KEY == 'YOUR_NEWS_API_KEY':
        return {
            'status': 'success',
            'news': [],
            'message': 'News API key not configured. Please set NEWS_API_KEY environment variable.'
        }
    
    try:
        # Search for both company name and ticker
        search_query = f'"{company_name}" OR "{ticker}"'
        url = f"https://newsapi.org/v2/everything?q={search_query}&apiKey={NEWS_API_KEY}&sortBy=publishedAt&pageSize=5&language=en"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') == 'ok' and data.get('totalResults', 0) > 0:
            news_items = []
            for article in data['articles'][:5]:
                if article.get('title') and article.get('description'):
                    news_items.append({
                        'title': article['title'],
                        'description': article['description'][:200] + '...' if len(article['description']) > 200 else article['description'],
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', 'Unknown')
                    })
            
            return {
                'status': 'success',
                'news': news_items
            }
        else:
            return {
                'status': 'success',
                'news': [],
                'message': f'No recent news found for {company_name} ({ticker})'
            }
    except Exception as e:
        return {
            'status': 'error',
            'error_message': f"Failed to fetch news: {str(e)}"
        }

def ticker_price(ticker: str) -> Dict[str, Any]:
    """Get current stock price"""
    if ALPHA_VANTAGE_API_KEY == 'YOUR_API_KEY':
        return {
            'status': 'error',
            'error_message': 'Alpha Vantage API key not configured. Please set ALPHA_VANTAGE_API_KEY environment variable.'
        }
    
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'Global Quote' in data:
            quote = data['Global Quote']
            if '05. price' in quote:
                return {
                    'status': 'success',
                    'ticker': ticker,
                    'current_price': float(quote['05. price']),
                    'change': float(quote.get('09. change', 0)),
                    'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                    'volume': int(quote.get('06. volume', 0)),
                    'latest_trading_day': quote.get('07. latest trading day', ''),
                    'previous_close': float(quote.get('08. previous close', 0))
                }
        
        # Fallback to daily data if quote fails
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}&outputsize=compact"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'Time Series (Daily)' in data:
            daily_data = data['Time Series (Daily)']
            latest_date = max(daily_data.keys())
            latest_data = daily_data[latest_date]
            
            return {
                'status': 'success',
                'ticker': ticker,
                'current_price': float(latest_data['4. close']),
                'high': float(latest_data['2. high']),
                'low': float(latest_data['3. low']),
                'volume': int(latest_data['5. volume']),
                'latest_trading_day': latest_date,
                'open': float(latest_data['1. open'])
            }
        
        return {
            'status': 'error',
            'error_message': f'Could not retrieve price data for {ticker}. API might be rate limited or ticker not found.'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error_message': f"Failed to fetch stock price: {str(e)}"
        }

def get_historical_data(ticker: str, function: str, interval: str = None) -> Dict[str, Any]:
    """Helper function to get historical data"""
    if ALPHA_VANTAGE_API_KEY == 'YOUR_API_KEY':
        return {}
    
    try:
        url = f"https://www.alphavantage.co/query?function={function}&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}&outputsize=compact"
        if interval:
            url += f"&interval={interval}"
        
        response = requests.get(url, timeout=15)
        data = response.json()
        
        # Handle different time series keys
        time_series_keys = {
            'TIME_SERIES_INTRADAY': f'Time Series ({interval})',
            'TIME_SERIES_DAILY': 'Time Series (Daily)',
            'TIME_SERIES_WEEKLY': 'Weekly Time Series',
            'TIME_SERIES_MONTHLY': 'Monthly Time Series'
        }
        
        key = time_series_keys.get(function)
        if key and key in data:
            return data[key]
        
        # Handle API errors
        if 'Error Message' in data:
            print(f"API Error: {data['Error Message']}")
        elif 'Note' in data:
            print(f"API Note: {data['Note']}")
        
        return {}
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return {}

def ticker_price_change(ticker: str, timeframe: str = '1week') -> Dict[str, Any]:
    """Calculate price change over specified timeframe"""
    try:
        timeframe = timeframe.lower()
        
        if timeframe in ['today', '1day', '1d', 'day']:
    
            time_series = get_historical_data(ticker, 'TIME_SERIES_DAILY')
            if not time_series:
                return {
                    'status': 'error',
                    'error_message': 'No daily data available - API might be rate limited'
                }
            
            dates = sorted(time_series.keys(), reverse=True)
            if len(dates) < 2:
                return {
                    'status': 'error',
                    'error_message': 'Not enough trading days available'
                }
            
            current_close = float(time_series[dates[0]]['4. close'])
            previous_close = float(time_series[dates[1]]['4. close'])
            price_change = current_close - previous_close
            percent_change = (price_change / previous_close) * 100
            
            return {
                'status': 'success',
                'price_change': price_change,
                'percent_change': percent_change,
                'timeframe': 'daily',
                'previous_close': previous_close,
                'current_close': current_close,
                'current_date': dates[0],
                'previous_date': dates[1]
            }
        
        elif timeframe in ['week', '1week', '1w', '7days']:
    
            time_series = get_historical_data(ticker, 'TIME_SERIES_DAILY')
            if not time_series:
                return {
                    'status': 'error',
                    'error_message': 'No daily data available for weekly calculation'
                }
            
            dates = sorted(time_series.keys(), reverse=True)
            if len(dates) < 5:  
                return {
                    'status': 'error',
                    'error_message': 'Not enough trading days available for weekly comparison'
                }
            
            current_close = float(time_series[dates[0]]['4. close'])
    
            week_ago_close = float(time_series[dates[min(4, len(dates)-1)]]['4. close'])
            price_change = current_close - week_ago_close
            percent_change = (price_change / week_ago_close) * 100
            
            return {
                'status': 'success',
                'price_change': price_change,
                'percent_change': percent_change,
                'timeframe': 'weekly',
                'previous_close': week_ago_close,
                'current_close': current_close,
                'current_date': dates[0],
                'previous_date': dates[min(4, len(dates)-1)]
            }
        
        elif timeframe in ['month', '1month', '1m', '30days']:
            time_series = get_historical_data(ticker, 'TIME_SERIES_DAILY')
            if not time_series:
                return {
                    'status': 'error',
                    'error_message': 'No daily data available for monthly calculation'
                }
            
            dates = sorted(time_series.keys(), reverse=True)
            if len(dates) < 20:  
                return {
                    'status': 'error',
                    'error_message': 'Not enough trading days available for monthly comparison'
                }
            
            current_close = float(time_series[dates[0]]['4. close'])
            # Get price from ~20 trading days ago (1 month)
            month_ago_close = float(time_series[dates[min(19, len(dates)-1)]]['4. close'])
            price_change = current_close - month_ago_close
            percent_change = (price_change / month_ago_close) * 100
            
            return {
                'status': 'success',
                'price_change': price_change,
                'percent_change': percent_change,
                'timeframe': 'monthly',
                'previous_close': month_ago_close,
                'current_close': current_close,
                'current_date': dates[0],
                'previous_date': dates[min(19, len(dates)-1)]
            }
        else:
            return {
                'status': 'error',
                'error_message': f"Unsupported timeframe: {timeframe}. Supported: 1day, 1week, 1month"
            }
    except Exception as e:
        return {
            'status': 'error',
            'error_message': f"Failed to calculate price change: {str(e)}"
        }

def ticker_analysis(ticker: str, company_name: str, timeframe: str = '1week') -> Dict[str, Any]:
    """Analyze and summarize reason behind recent price movements"""
    
    # Get current price
    price_data = ticker_price(ticker)
    if price_data['status'] != 'success':
        return {
            'status': 'error',
            'error_message': f"Could not get current price: {price_data.get('error_message', 'Unknown error')}"
        }
    
    # Get price change
    price_change_data = ticker_price_change(ticker, timeframe)
    if price_change_data['status'] != 'success':
        return {
            'status': 'error',
            'error_message': f"Could not get price change: {price_change_data.get('error_message', 'Unknown error')}"
        }
    
    news_data = ticker_news(ticker, company_name)

    current_price = price_data['current_price']
    price_change = price_change_data['price_change']
    percent_change = price_change_data['percent_change']
    
    # Determine trend description
    if percent_change > 5:
        trend = "significant increase"
        trend_emoji = "📈"
    elif percent_change > 2:
        trend = "moderate increase"
        trend_emoji = "📈"
    elif percent_change > 0:
        trend = "slight increase"
        trend_emoji = "📊"
    elif percent_change < -5:
        trend = "significant decrease"
        trend_emoji = "📉"
    elif percent_change < -2:
        trend = "moderate decrease"
        trend_emoji = "📉"
    elif percent_change < 0:
        trend = "slight decrease"
        trend_emoji = "📊"
    else:
        trend = "minimal change"
        trend_emoji = "➡️"

    analysis_parts = []
    
    analysis_parts.append(f"{trend_emoji} **{company_name} ({ticker}) Stock Analysis**")
    analysis_parts.append(f"Current Price: ${current_price:.2f}")
    analysis_parts.append(f"{timeframe.title()} Change: ${price_change:+.2f} ({percent_change:+.2f}%)")
    analysis_parts.append(f"Trend: {trend}")
    
    # Time period context
    if 'current_date' in price_change_data and 'previous_date' in price_change_data:
        analysis_parts.append(f"Period: {price_change_data['previous_date']} to {price_change_data['current_date']}")
    
    # News analysis
    if news_data['status'] == 'success' and news_data.get('news'):
        analysis_parts.append("\n**Recent News Impact:**")
        relevant_keywords = ['earnings', 'revenue', 'profit', 'loss', 'beat', 'miss', 'guidance', 
                           'upgrade', 'downgrade', 'analyst', 'target', 'partnership', 'deal', 
                           'acquisition', 'merger', 'lawsuit', 'regulation', 'fda', 'approval']
        
        relevant_news = []
        for news_item in news_data['news'][:3]:
            title_lower = news_item['title'].lower()
            if any(keyword in title_lower for keyword in relevant_keywords):
                relevant_news.append(news_item)
        
        if relevant_news:
            for i, news_item in enumerate(relevant_news, 1):
                pub_date = news_item['published_at'][:10] if news_item['published_at'] else 'Recent'
                analysis_parts.append(f"{i}. {news_item['title']} ({pub_date})")
                if news_item['description']:
                    analysis_parts.append(f"   {news_item['description']}")
        else:
            analysis_parts.append("No major news events found that clearly correlate with the price movement.")
    else:
        analysis_parts.append(f"\n**News:** {news_data.get('message', 'Unable to fetch recent news')}")
    
    # Investment context
    analysis_parts.append(f"\n**Investment Context:**")
    if abs(percent_change) > 5:
        analysis_parts.append("This represents a significant price movement that may warrant attention from investors.")
    elif abs(percent_change) > 2:
        analysis_parts.append("This shows moderate price volatility typical of active trading.")
    else:
        analysis_parts.append("This reflects relatively stable price action with minimal volatility.")
    
    final_analysis = "\n".join(analysis_parts)
    
    return {
        'status': 'success',
        'analysis': final_analysis,
        'current_price': current_price,
        'price_change': price_change,
        'percent_change': percent_change,
        'timeframe': timeframe,
        'trend': trend,
        'news_count': len(news_data.get('news', [])) if news_data['status'] == 'success' else 0
    }

# Root Agent Configuration
root_agent = Agent(
    name="stock_analysis_agent",
    model="gemini-2.0-flash",
    description="Comprehensive stock market analysis agent with real-time data and news integration",
    instruction=(
        "You are an advanced stock analysis agent capable of:\n"
        "1. Identifying stock tickers from company names or symbols\n"
        "2. Retrieving current stock prices and trading data\n"
        "3. Calculating price changes over various timeframes (daily, weekly, monthly)\n"
        "4. Fetching relevant financial news and market updates\n"
        "5. Providing comprehensive analysis of stock performance with context\n\n"
        "When users ask about stocks, always:\n"
        "- First identify the correct ticker symbol\n"
        "- Get current price information\n"
        "- Calculate relevant price changes\n"
        "- Gather recent news if available\n"
        "- Provide a comprehensive analysis explaining the movements\n\n"
        "Handle queries like:\n"
        "- 'How is Tesla doing today?'\n"
        "- 'Why did NVDA drop this week?'\n"
        "- 'What's the latest on Apple stock?'\n"
        "- 'Analyze Microsoft's recent performance'\n\n"
        "Always provide context, explanations, and actionable insights.\n"
        "If API keys are not configured, inform the user about limitations."
    ),
    tools=[identify_ticker, ticker_news, ticker_price, ticker_price_change, ticker_analysis]
)

if __name__ == '__main__':
    print("Testing Stock Analysis Agent...")
    
    test_query = "How is Tesla doing today?"
    ticker_result = identify_ticker(test_query)
    print(f"Ticker identification result: {ticker_result}")
    
    if ticker_result['status'] == 'success':
        ticker = ticker_result['ticker']
        company_name = ticker_result['company_name']
        
        analysis_result = ticker_analysis(ticker, company_name, '1day')
        print(f"\nAnalysis result: {analysis_result}")
    
    root_agent.serve()