import os
from google.adk.agents import Agent
from typing import Dict, Any, Optional
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass

# Configuration
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

# Subagent Functions
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
        'meta': 'META',
        'netflix': 'NFLX'
    }
    
    query_lower = query.lower()
    matched_ticker = None
    company_name = None
    
    for name, ticker in ticker_mapping.items():
        if name in query_lower:
            matched_ticker = ticker
            company_name = name.capitalize()
            break
    
    if not matched_ticker:
        try:
            url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url)
            data = response.json()
            
            if 'bestMatches' in data and len(data['bestMatches']) > 0:
                matched_ticker = data['bestMatches'][0]['1. symbol']
                company_name = data['bestMatches'][0]['2. name']
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f"Error searching for ticker: {e}"
            }
    
    if not matched_ticker:
        return {
            'status': 'error',
            'error_message': 'Could not identify stock ticker from query'
        }
    
    return {
        'status': 'success',
        'ticker': matched_ticker,
        'company_name': company_name
    }

def ticker_news(ticker: str, company_name: str) -> Dict[str, Any]:
    """Retrieve recent news about the stock"""
    try:
        url = f"https://newsapi.org/v2/everything?q={company_name} OR {ticker}&apiKey={NEWS_API_KEY}&sortBy=publishedAt&pageSize=3"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'ok' and data['totalResults'] > 0:
            news_items = [{
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'published_at': article['publishedAt']
            } for article in data['articles'][:3]]
            
            return {
                'status': 'success',
                'news': news_items
            }
        return {
            'status': 'success',
            'news': [],
            'message': 'No recent news found'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error_message': f"Failed to fetch news: {str(e)}"
        }

def ticker_price(ticker: str) -> Dict[str, Any]:
    """Fetch current stock price"""
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if 'Global Quote' in data:
            return {
                'status': 'success',
                'current_price': float(data['Global Quote']['05. price'])
            }
        return {
            'status': 'error',
            'error_message': 'Could not fetch current price'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error_message': f"Failed to fetch price: {str(e)}"
        }

def ticker_price_change(ticker: str, timeframe: str = '1week') -> Dict[str, Any]:
    """Calculate price change over specified timeframe"""
    try:
        if timeframe in ['today', '1day']:
            function = 'TIME_SERIES_INTRADAY'
            interval = '60min'
        elif timeframe in ['week', '1week']:
            function = 'TIME_SERIES_DAILY'
            days_to_fetch = 7
        elif timeframe in ['month', '1month']:
            function = 'TIME_SERIES_DAILY'
            days_to_fetch = 30
        else:
            return {
                'status': 'error',
                'error_message': f"Unsupported timeframe: {timeframe}"
            }
        
        url = f"https://www.alphavantage.co/query?function={function}&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        if function == 'TIME_SERIES_INTRADAY':
            url += f"&interval={interval}"
        
        response = requests.get(url)
        data = response.json()
        
        if function == 'TIME_SERIES_INTRADAY':
            time_series = data.get(f'Time Series ({interval})', {})
            today = datetime.now().date()
            today_data = {k: v for k, v in time_series.items() if datetime.strptime(k, '%Y-%m-%d %H:%M:%S').date() == today}
            
            if not today_data:
                return {
                    'status': 'error',
                    'error_message': 'No intraday data available for today'
                }
            
            sorted_times = sorted(today_data.keys())
            open_price = float(today_data[sorted_times[0]]['1. open'])
            current_price = float(today_data[sorted_times[-1]]['4. close'])
            
            return {
                'status': 'success',
                'price_change': current_price - open_price,
                'percent_change': ((current_price - open_price) / open_price) * 100,
                'timeframe': timeframe
            }
        else:
            time_series = data.get('Time Series (Daily)', {})
            dates = sorted(time_series.keys(), reverse=True)[:days_to_fetch]
            
            if len(dates) < 2:
                return {
                    'status': 'error',
                    'error_message': 'Not enough historical data available'
                }
            
            oldest_price = float(time_series[dates[-1]]['4. close'])
            newest_price = float(time_series[dates[0]]['4. close'])
            
            return {
                'status': 'success',
                'price_change': newest_price - oldest_price,
                'percent_change': ((newest_price - oldest_price) / oldest_price) * 100,
                'timeframe': timeframe
            }
    except Exception as e:
        return {
            'status': 'error',
            'error_message': f"Failed to calculate price change: {str(e)}"
        }

def ticker_analysis(ticker: str, company_name: str, timeframe: str = '1week') -> Dict[str, Any]:
    """Analyze and summarize reason behind recent price movements"""
    price_result = ticker_price_change(ticker, timeframe)
    if price_result['status'] != 'success':
        return price_result
    
    news_result = ticker_news(ticker, company_name)
    if news_result['status'] != 'success':
        return news_result
    
    trend = "significant increase" if price_result['percent_change'] > 5 else \
            "moderate increase" if price_result['percent_change'] > 1 else \
            "significant decrease" if price_result['percent_change'] < -5 else \
            "moderate decrease" if price_result['percent_change'] < -1 else \
            "little change"
    
    relevant_news = []
    if news_result.get('news'):
        keywords = ['earnings', 'report', 'results', 'launch', 'deal', 'partnership', 
                   'ceo', 'cfo', 'resign', 'hire', 'forecast', 'upgrade', 'downgrade',
                   'analyst', 'rating', 'target', 'price']
        relevant_news = [
            news for news in news_result['news']
            if any(keyword in news['title'].lower() for keyword in keywords)
        ]
    
    analysis_text = f"{company_name} ({ticker}) has seen a {trend} in its stock price over the {timeframe} period. "
    analysis_text += f"The price changed by {price_result['price_change']:.2f} ({price_result['percent_change']:.2f}%) "
    
    if timeframe == '1day':
        analysis_text += "today. "
    elif timeframe == '1week':
        analysis_text += "in the past week. "
    elif timeframe == '1month':
        analysis_text += "in the past month. "
    
    if relevant_news:
        analysis_text += "This movement may be related to the following recent news:\n"
        for i, news_item in enumerate(relevant_news[:3], 1):
            analysis_text += f"{i}. {news_item['title']} (Published: {news_item['published_at'][:10]})\n"
    else:
        analysis_text += "No significant news events were found that clearly explain this price movement."
    
    return {
        'status': 'success',
        'analysis': analysis_text,
        'key_news': relevant_news[:3],
        'price_change': price_result['price_change'],
        'percent_change': price_result['percent_change'],
        'timeframe': timeframe
    }

# Root Agent Configuration
root_agent = Agent(
    name="stock_analysis_agent",
    model="gemini-2.0-flash",
    description="Multi-agent system for comprehensive stock market analysis",
    instruction=(
        "You are a sophisticated stock analysis agent that can:\n"
        "1. Identify company ticker symbols from names\n"
        "2. Retrieve current stock prices\n"
        "3. Fetch relevant financial news\n"
        "4. Calculate price changes over time\n"
        "5. Analyze and explain stock performance\n\n"
        "Handle queries like:\n"
        "- 'Why did Tesla stock drop today?'\n"
        "- 'What's happening with Palantir stock recently?'\n"
        "- 'How has Nvidia stock changed in the last 7 days?'\n\n"
        "Always provide accurate, well-reasoned analysis with supporting data."
    ),
    tools=[identify_ticker, ticker_news, ticker_price, ticker_price_change, ticker_analysis]
)

if __name__ == '__main__':
    # This will start the ADK web interface
    root_agent.serve()