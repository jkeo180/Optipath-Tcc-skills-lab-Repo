from xml.parsers.expat import model

from langgraph.prebuilt import create_react_agent

from medical_access import get_medical_access
from dataclasses import dataclass
from xmlrpc import client
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool,ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy
from dotenv import load_dotenv
from anthropic import Anthropic
import os
from pathlib import Path
import random
import pandas as pd



# ENV 
load_dotenv()
if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError("ANTHROPIC_API_KEY not found. Check your .env file.")

#  MODEL 
#model = Anthropic().messages.create(
#    model="claude-haiku-4-5-20251001",
#    max_tokens=10,
#    messages=[{"role": "user", "content": "Hello"}]
#)
client = Anthropic()
#print("API connection successful!")
# LOAD DATA ONCE 
df = pd.read_csv("PLACES__Local_Data_for_Better_Health,_Census_Tract_Data,_2025_release_20260324.csv")
df['StateAbbr']   = df['StateAbbr'].astype(str).str.strip().str.upper()
df['CountyName']  = df['CountyName'].astype(str).str.strip()
df['Data_Value']  = pd.to_numeric(df['Data_Value'], errors='coerce')

# TOOLS 

@tool
def get_health_data(location: str) -> str:
    """
    Get health indicator data for a given city or county.
    Input should be a city name like 'Houston' or 'Tacoma'.
    Returns top health conditions and their prevalence rates.
    """
    filtered = df[df['CountyName'].str.contains(location, case=False, na=False)]

    if filtered.empty:
        return f"No data found for {location}. Try a county name like 'Harris' for Houston."

    summary = (
        filtered.groupby('Short_Question_Text')['Data_Value']
        .mean()
        .dropna()
        .sort_values(ascending=False)
        .head(10)
    )

    result = f"Top health indicators for {location}:\n"
    for indicator, value in summary.items():
        result += f"  {indicator}: {value:.1f}%\n"
    return result

@tool
def compare_locations(location1: str, location2: str) -> str:
    """
    Compare health indicators between two cities or counties.
    Input should be two city or county names separated by a comma.
    """
    def get_summary(loc):
        filtered = df[df['CountyName'].str.contains(loc, case=False, na=False)]
        if filtered.empty:
            return None
        return (
            filtered.groupby('Short_Question_Text')['Data_Value']
            .mean()
            .dropna()
            .sort_values(ascending=False)
            .head(5)
        )
@tool
def quantify_zip_risk(zip_code: str) -> str:
    """
    Quantifies health risk for a specific ZIP code (ZCTA) relative to the 
    national average. Returns a Risk Index (1.0 = National Average).
    """
    # Ensure ZIP is a string and matches the ZCTA format in the CDC dataset
    target_zip = str(zip_code).strip().zfill(5)
    
    # 1. Calculate National Averages (Run this once globally for speed)
    national_means = df.groupby('MeasureId')['Data_Value'].mean()
    
    # 2. Filter for the specific ZIP Code Tabulation Area
    zip_data = df[df['ZCTA5'] == target_zip]
    
    if zip_data.empty:
        return f"No health data available for ZIP code {target_zip}."
    
    # 3. Calculate Risk Index (Local / National)
    zip_means = zip_data.groupby('MeasureId')['Data_Value'].mean()
    risk_index = (zip_means / national_means).dropna().sort_values(ascending=False)
    
    result = f"Health Risk Quantification for ZIP {target_zip}:\n"
    result += "(> 1.0 indicates higher prevalence than the national average)\n\n"
    
    # Show top 5 risk factors in this ZIP
    for measure, index in risk_index.head(5).items():
        severity = "🔴 HIGH" if index > 1.5 else "🟡 MODERATE"
        result += f" - {measure}: {index:.2f}x national avg ({severity})\n"
        
    return result
# SYSTEM PROMPT 
SYSTEM_PROMPT = """You are OptiPath, a health data assistant for insurance providers and healthcare consultants.

You help users understand the health landscape of any community in the United States.
You have access to CDC health data covering diabetes, heart disease, food access, poverty and more.

When a user asks about a city, use get_health_data to retrieve indicators for that area.
When a user wants to compare two cities, use compare_locations.
Always respond in plain English. No jargon. Be concise and helpful.
If you don't find data for a city name, suggest trying the county name instead."""

# AGENT
def hub():
    return client.ServerProxy("https://hub.langgraph.com/rpc")
prompt = hub.pull("hwchase17/react")

# 2. Initialize the ReAct agent
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
agent = create_react_agent(
    llm=model,
    tools=[get_health_data, compare_locations, quantify_zip_risk],
    prompt=prompt
)

# 3. Initialize the Executor
# It is a class instance, not a function call
agent_executor = AgentExecutor(
    agent=agent,
    tools=[get_health_data, compare_locations, quantify_zip_risk],
    verbose=True,
    handle_parsing_errors=True # Recommended for ReAct agents
)

# 4. Invoke the agent
if __name__ == "__main__":
    # Ensure the input key matches what the prompt expects (usually 'input')
    response = agent_executor.invoke({
        "input": "What are the biggest health concerns in Houston, Texas?"
    })
    print(response["output"])
