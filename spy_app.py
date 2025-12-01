import streamlit as st
import os
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.tools import FunctionTool
from tavily import TavilyClient
import yfinance as yf
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION & CSS ---
st.set_page_config(page_title="Stratagem AI", page_icon="🌐", layout="wide")
load_dotenv()

# Custom CSS for "Professional Fintech" Look
st.markdown("""
    <style>
    /* Main Background adjustments */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Header Styling */
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        color: #FFFFFF;
    }
    h3 {
        color: #A0AAB5;
    }
    
    /* Custom Button Styling */
    div.stButton > button:first-child {
        background: linear-gradient(to right, #00C853, #64DD17);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 0.5em 1em;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:first-child:hover {
        transform: scale(1.05);
        box-shadow: 0px 4px 15px rgba(0, 200, 83, 0.4);
    }

    /* Card-like styling for report */
    .report-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00C853;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        color: #E0E0E0;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. SETUP API KEYS ---
openai_key = os.getenv("OPENAI_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

if not openai_key:
    if "OPENAI_API_KEY" in st.secrets:
        openai_key = st.secrets["OPENAI_API_KEY"]
        tavily_key = st.secrets["TAVILY_API_KEY"]
    else:
        st.error("🚨 Missing API Keys! Please check your .env file.")
        st.stop()

llm = OpenAI(model="gpt-4o-mini", api_key=openai_key)
tavily = TavilyClient(api_key=tavily_key)


# --- 2. DEFINE INTELLIGENT TOOLS (With Clean UI Feedback) ---

def web_search(query: str) -> str:
    """Useful for finding latest news, leaks, or product announcements."""
    st.toast(f"🌍 Searching Google: {query}...", icon="🔍")
    try:
        response = tavily.search(query=query, search_depth="advanced")
        context = [obj["content"] for obj in response["results"]]
        return "\n\n".join(context)
    except Exception as e:
        return f"Search failed: {e}"

def get_stock_info(ticker: str) -> str:
    """Useful for getting live stock prices and financial ratios."""
    st.toast(f"📈 Reading Market Data: {ticker}...", icon="📊")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return f"""
        Current Price: ${info.get('currentPrice', 'N/A')}
        Market Cap: ${info.get('marketCap', 'N/A')}
        52 Week High: ${info.get('fiftyTwoWeekHigh', 'N/A')}
        Recommendation: {info.get('recommendationKey', 'N/A')}
        """
    except Exception as e:
        return f"Stock fetch failed: {e}"

def scrape_pricing_page(url: str) -> str:
    """Useful for reading specific website pages to get detailed text."""
    st.toast(f"👀 Analyzing Website: {url}...", icon="🕸️")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return '\n'.join(chunk for chunk in chunks if chunk)[:5000] 
    except Exception as e:
        return f"Error scraping: {e}"

# --- 3. BUILD THE UI ---

# Sidebar Navigation
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/825/825590.png", width=50) # Placeholder Icon
    st.markdown("## Control Center")
    st.markdown("---")
    
    target_company = st.text_input("🎯 Target Asset", value="Nvidia", placeholder="e.g. Tesla, Apple")
    
    mission_goal = st.pills("Select Objective", 
        ["General Analysis", "Find Weaknesses", "Product Pricing", "Leadership Scandal"],
        default="General Analysis"
    )
    
    st.markdown("---")
    start_btn = st.button("Initialize Stratagem 🚀", type="primary", use_container_width=True)
    st.caption("v2.1.0 | Enterprise Edition")

# Main Content Area
col1, col2 = st.columns([3, 1])

with col1:
    st.title("Stratagem AI")
    st.markdown("### Market Intelligence & Competitor Reconnaissance")

with col2:
    # Just a visual placeholder for status
    st.markdown("") 

# --- 4. MAIN AGENT LOGIC ---

if start_btn and target_company:
    
    st.divider()
    
    # Improved Status Container
    with st.status(f"⚡ **Stratagem Active:** Analyzing {target_company}...", expanded=True) as status:
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.write("⚙️ **Initializing Agents...**")
        
        # Initialize Tools & Agent
        tools = [
            FunctionTool.from_defaults(fn=web_search),
            FunctionTool.from_defaults(fn=get_stock_info),
            FunctionTool.from_defaults(fn=scrape_pricing_page)
        ]
        
        agent = OpenAIAgent.from_tools(
            tools,
            llm=llm,
            verbose=True,
            system_prompt=f"""
            You are Stratagem, an elite Market Intelligence Analyst.
            Target: {target_company}
            Goal: {mission_goal}
            
            Format your report cleanly with Markdown headers (##), bullet points, and bold text for key metrics.
            Always end with a 'Strategic Verdict' section.
            """
        )
        
        response = agent.chat(f"Execute comprehensive analysis on {target_company}. Focus area: {mission_goal}")
        
        status.update(label="✅ Analysis Complete", state="complete", expanded=False)

    # --- 5. DISPLAY & DOWNLOAD RESULTS ---
    
    # Use the custom CSS class for the card
    st.markdown(f"""
    <div class="report-card">
        <h2>📂 Intelligence Dossier: {target_company.upper()}</h2>
        <p><strong>Objective:</strong> {mission_goal}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display the result
    st.markdown(response.response)
    
    st.markdown("---")
    
    # Download Button logic
    filename = f"Stratagem_{target_company}_Report.md"
    st.download_button(
        label="📥 Export Dossier (Markdown)",
        data=response.response,
        file_name=filename,
        mime="text/markdown"
    )

elif start_btn and not target_company:
    st.warning("⚠️ Protocol Halted: Please define a Target Asset.")