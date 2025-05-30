# Stock Analysis Agent

This repository provides tools and agents for stock analysis using modular Python components. It supports both multi-tool agent workflows and dedicated stock analysis agents, making it flexible for a variety of financial data analysis tasks.

## ✨ Features

- **Multi-tool Agent Framework**: Combine different tools and agents for composite workflows.
- **Stock Analysis Agent**: Specialized modules focused on stock market data analysis.
- **Extensible & Pythonic**: Easy to expand and integrate into bigger projects.
- **AI-Powered**: Integrates with Google Gemini API and Vertex AI for advanced insights.

## 🤔 What Can You Ask This Agent?

Ask questions like:
1. 📈 **"Show me the latest trends for Apple stock."**
2. 🕵️‍♂️ **"Compare Google and Amazon stock performance in the last year."**
3. 📰 **"Summarize the latest news for Tesla."**
4. 🧠 **"Predict tomorrow’s movement for Microsoft based on recent data."**

*If it’s about stocks, analysis, or financial data—try it!*

## 🗂️ Project Structure

```
.
├── multi_tool_agent/
│   └── __init__.py
├── stock_anaylsis_agent/
│   └── __init__.py
├── .gitignore
├── Readme.md
```

## 🚀 Installation

```bash
git clone https://github.com/avanshh99/stock_analysis_agent.git
cd stock_analysis_agent

# (Recommended) Use a virtual environment (windows):
python3 -m venv venv
source venv/bin/activate

## 🔑 Adding API Keys

Some features need API keys (for real-time data & AI):

1. Create a `.env` file in the project root.
2. Add keys like:

   ```
   # Stock/financial data providers
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
   FINNHUB_API_KEY=your_finnhub_key_here

   # Google Gemini API (for Gemini Pro & Gemini 1.5)
   GOOGLE_API_KEY=your_google_gemini_api_key_here
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
   
   ```

3. Install `python-dotenv` if needed.

## 🛠️ Usage

Import and extend in your own scripts or notebooks:

```python
from stock_anaylsis_agent import agent as stock_agent
from multi_tool_agent import agent as multi_tool

# Examples:
# stock_agent.analyze('AAPL')
# multi_tool.run_custom_workflow(...)
```
## 🏁 Running the Agent

To launch the agent using Google ADK’s web interface, simply run the following command in your terminal:

```bash
adk web
```

This will start the ADK web server, allowing you to interact with your agents through a browser UI.

If you want to run the agent module directly (for example, for testing):

```bash
python -m stock_anaylsis_agent.agent
```

## 🤝 Contributing

Pull requests, issues, and stars are all welcome!

**Built with ❤️ by Avan**
