import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import json
from typing import Dict, List, Tuple, Optional

# LLM Integration
try:
    from openai import OpenAI
    from dotenv import load_dotenv
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    st.warning("LLM packages not installed. Install with: pip install openai python-dotenv")

# Set page configuration
st.set_page_config(
    page_title="Healthcare AI Assistant Demo",
    page_icon="⚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

class LLMProcessor:
    def __init__(self):
        self.client = None
        self.available = False
        self.demo_mode = False
        self.init_llm()
    
    def init_llm(self):
        """Initialize LLM client"""
        if not LLM_AVAILABLE:
            return
        
        try:
            # Try to load from environment first
            if os.path.exists('.env'):
                load_dotenv()
            
            # Check if demo mode is enabled
            if os.getenv("DEMO_MODE", "false").lower() == "true":
                self.demo_mode = True
                self.available = True
                print("LLM initialized in DEMO MODE (enhanced rule-based responses)")
                return
            
            # Get configuration from environment
            base_url = os.getenv("OPENAI_BASE_URL")
            api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                print("WARNING: No OPENAI_API_KEY found. Falling back to demo mode.")
                self.demo_mode = True
                self.available = True
                return
            
            # Initialize OpenAI client
            if base_url:
                self.client = OpenAI(base_url=base_url, api_key=api_key)
            else:
                self.client = OpenAI(api_key=api_key)
                
            # Test the connection
            test_response = self.client.chat.completions.create(
                model="kaz-22a",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            self.available = True
            print("LLM initialized successfully with API")
            
        except Exception as e:
            print(f"WARNING: LLM API initialization failed: {e}")
            print("Falling back to demo mode...")
            self.demo_mode = True
            self.available = True
    
    def get_available_functions(self):
        """Define available functions for the LLM to call"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_sales_trend",
                    "description": "Analyze sales trends and performance over time. Use this when users ask about trends, performance, sales data for specific drugs, or want to see how a drug is performing. Also use for simple drug mentions like 'aspirin' or 'aspirin sales'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {
                                "type": "string",
                                "description": "Name of the drug to analyze. Available drugs: Aspirin, Ibuprofen, Medication X, Allergy Relief, Blood Pressure Med, Diabetes Control, Antibiotic Plus, Vitamin D3. Leave empty for all drugs."
                            },
                            "region": {
                                "type": "string",
                                "description": "Region to filter analysis by. Available regions: North America, Europe, Asia, South America. Leave empty for all regions."
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_drugs",
                    "description": "Compare performance between multiple drugs. Use when users ask to compare drugs, see which drugs perform better, or want comparative analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "region": {
                                "type": "string",
                                "description": "Region to filter comparison by. Available regions: North America, Europe, Asia, South America. Leave empty for global comparison."
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "regional_analysis",
                    "description": "Analyze sales performance across different regions. Use when users ask about regional performance, geographic analysis, or how different regions are performing.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {
                                "type": "string",
                                "description": "Name of the drug to analyze by region. Available drugs: Aspirin, Ibuprofen, Medication X, Allergy Relief, Blood Pressure Med, Diabetes Control, Antibiotic Plus, Vitamin D3. Leave empty for all drugs."
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_auto_insights",
                    "description": "Generate comprehensive business insights and interesting findings from all available data. Use when users ask for insights, interesting findings, business overview, or general analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "answer_direct_question",
                    "description": "Answer specific direct questions about the business data like 'what is our best seller', 'total revenue', 'worst performer', etc. Use for factual questions that need specific data points.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The specific question being asked by the user"
                            }
                        }
                    }
                }
            }
        ]
    
    def _demo_function_calling(self, query: str) -> Dict:
        """Enhanced demo mode with intelligent function calling simulation"""
        query_lower = query.lower()
        
        # Conversational responses (no function calling) - using word boundaries
        if any(f" {greeting} " in f" {query_lower} " for greeting in ["hello", "hi", "hey"]) or any(phrase in query_lower for phrase in ["good morning", "good afternoon"]):
            return {
                "type": "conversational",
                "response": "Hello! I'm your healthcare AI assistant. I can help you analyze sales data, create visualizations, and provide business insights. What would you like to know about today?"
            }
        
        if any(phrase in query_lower for phrase in ["how are you", "how's it going", "what's up"]):
            return {
                "type": "conversational", 
                "response": "I'm doing great, thank you for asking! I'm here to help you with healthcare sales analysis. I can show you trends, compare drug performance, analyze regional data, or answer specific questions about your business. What would you like to explore?"
            }
        
        if any(phrase in query_lower for phrase in ["what can you do", "what can you help", "how can you help", "what are your capabilities"]):
            return {
                "type": "conversational",
                "response": """I can help you with several types of healthcare sales analysis:

**Sales Trend Analysis** - Track how drugs perform over time
**Drug Comparisons** - Compare performance between different medications  
**Regional Analysis** - See how different regions are performing
**Business Insights** - Get automatic insights and interesting findings
**Direct Questions** - Answer specific questions like "What's our best seller?"

Try asking something like:
- "Show me sales trends for Aspirin"
- "Compare drug performance" 
- "Which is our best selling drug?"
- "Tell me something interesting about our business"
"""
            }
        
        if any(phrase in query_lower for phrase in ["thank you", "thanks", "appreciate"]):
            return {
                "type": "conversational",
                "response": "You're welcome! I'm always here to help with your healthcare data analysis needs. Feel free to ask me anything about sales trends, drug performance, or business insights!"
            }
        
        if any(phrase in query_lower for phrase in ["goodbye", "bye", "see you", "farewell"]):
            return {
                "type": "conversational", 
                "response": "Goodbye! It was great helping you with your healthcare data analysis. Come back anytime you need insights into your sales performance!"
            }
        
        # Function calling logic for business queries
        drugs = ["aspirin", "ibuprofen", "medication x", "allergy relief", 
                "blood pressure med", "diabetes control", "antibiotic plus", "vitamin d3"]
        regions = ["north america", "europe", "asia", "south america"]
        
        detected_drug = None
        detected_region = None
        
        for drug in drugs:
            if drug in query_lower:
                detected_drug = drug.title()
                break
                
        for region in regions:
            if region in query_lower:
                detected_region = region.title()
                break
        
        # Direct questions
        if (any(phrase in query_lower for phrase in ["best seller", "top performer", "highest sales", "worst seller", "total sales", "revenue", "how much", "how many"]) or 
            ("which" in query_lower and any(word in query_lower for word in ["best", "top", "highest", "lowest", "worst"])) or
            ("what" in query_lower and any(word in query_lower for word in ["best", "top", "highest", "total"]))):
            return {
                "type": "function_call",
                "function_name": "answer_direct_question",
                "function_args": {"question": query},
                "response": "Let me look that up for you in our sales data."
            }
        
        # Trend analysis
        elif any(word in query_lower for word in ["trend", "over time", "performance"]) or (any(word in query_lower for word in ["show", "display"]) and detected_drug):
            return {
                "type": "function_call",
                "function_name": "analyze_sales_trend", 
                "function_args": {"drug_name": detected_drug, "region": detected_region},
                "response": f"I'll analyze the sales trends for {detected_drug or 'all drugs'}" + (f" in {detected_region}" if detected_region else "") + "."
            }
        
        # Comparisons - improved detection
        elif (any(word in query_lower for word in ["compare", "comparison", "vs", "versus"]) or 
              ("all drug" in query_lower and "performance" in query_lower) or
              ("drug performance" in query_lower and "all" in query_lower)):
            return {
                "type": "function_call",
                "function_name": "compare_drugs",
                "function_args": {"region": detected_region},
                "response": "I'll compare the drug performance data for you."
            }
        
        # Regional analysis
        elif any(word in query_lower for word in ["region", "geography", "where", "location"]) and not any(phrase in query_lower for phrase in ["what can you do", "how can you help"]):
            return {
                "type": "function_call",
                "function_name": "regional_analysis",
                "function_args": {"drug_name": detected_drug},
                "response": f"I'll analyze regional performance{' for ' + detected_drug if detected_drug else ''}."
            }
        
        # Auto insights
        elif any(word in query_lower for word in ["insights", "interesting", "findings", "summary", "overview", "tell me about", "business", "general"]):
            return {
                "type": "function_call", 
                "function_name": "generate_auto_insights",
                "function_args": {},
                "response": "Let me analyze the data and show you some interesting insights about the healthcare business."
            }
        
        # Handle standalone drug queries (like "aspirin", "aspirin sales")
        elif detected_drug and not any(word in query_lower for word in ["hello", "hi", "thanks", "thank you", "goodbye", "bye"]):
            # For simple drug queries, default to trend analysis
            if (len(query_lower.split()) <= 3 and 
                any(phrase in query_lower for phrase in [detected_drug.lower(), "sales", "performance", "data", "info", "information"]) or
                query_lower.strip() == detected_drug.lower()):
                return {
                    "type": "function_call",
                    "function_name": "analyze_sales_trend",
                    "function_args": {"drug_name": detected_drug, "region": detected_region},
                    "response": f"I'll analyze the sales trends for {detected_drug}{' in ' + detected_region if detected_region else ''}."
                }
        
        # Default conversational response for unclear queries
        else:
            return {
                "type": "conversational",
                "response": "I'm not sure I understand what you're looking for. Could you be more specific? For example, you could ask about sales trends, drug comparisons, regional performance, or specific questions about the business data."
            }
    
    def process_query_with_functions(self, query: str, data_context: str = "", conversation_history: List[Dict] = None) -> Dict:
        """Process query using LLM with function calling capabilities and conversation context"""
        if not self.available:
            return {
                "type": "conversational",
                "response": "I'm sorry, but the LLM service is not available right now. Please check the configuration.",
                "error": True
            }
        
        # Use demo mode if enabled or client not available
        if self.demo_mode or self.client is None:
            return self._demo_function_calling_with_context(query, conversation_history or [])
        
        try:
            # Prepare conversation context for LLM
            messages = [
                {
                    "role": "system", 
                    "content": f"""You are an intelligent healthcare AI assistant specializing in pharmaceutical sales data analysis. You have full access to healthcare sales data and can perform sophisticated analyses using the available functions.

AVAILABLE DATA:
{data_context}

AVAILABLE DRUGS: Aspirin, Ibuprofen, Medication X, Allergy Relief, Blood Pressure Med, Diabetes Control, Antibiotic Plus, Vitamin D3
AVAILABLE REGIONS: North America, Europe, Asia, South America

YOUR CAPABILITIES:
You can analyze sales trends, compare drug performance, analyze regional data, generate business insights, and answer direct questions about the data.

FUNCTION CALLING GUIDELINES:
1. ALWAYS use functions for data analysis requests - never try to answer data questions without calling functions
2. For casual conversation, greetings, or general questions: respond conversationally WITHOUT calling functions
3. Use conversation context intelligently to understand follow-up questions and references

CONTEXT UNDERSTANDING EXAMPLES:
- User asks "Which is our best seller?" → Use answer_direct_question
- User follows up with "what about aspirin?" → Use analyze_sales_trend for Aspirin (understanding they want Aspirin analysis)
- User says "show that for Europe" → Apply Europe filter to the previous analysis type
- User mentions just "aspirin" or "aspirin sales" → Use analyze_sales_trend for Aspirin
- User asks "compare them" after drug discussion → Use compare_drugs
- User asks about "trends" or "performance" → Use analyze_sales_trend
- User asks for "insights" or "interesting findings" → Use generate_auto_insights
- User asks about "regions" or "geography" → Use regional_analysis

IMPORTANT: 
- Understand the full context of the conversation
- Don't just look for keywords - understand the user's intent
- When users reference previous analysis or ask follow-up questions, maintain context
- Be intelligent about parameter selection based on conversation flow
- Always provide helpful, brief responses when calling functions"""
                }
            ]
            
            # Add conversation history - keep more context for better understanding
            if conversation_history:
                # Add recent conversation context (last 8 messages for better context)
                recent_history = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
                for msg in recent_history:
                    # Keep more content for better context understanding
                    content = msg["content"]
                    if len(content) > 800:
                        # For very long messages, keep the beginning and summary
                        content = content[:400] + "\n...[analysis results]...\n" + content[-200:]
                    messages.append({
                        "role": msg["role"],
                        "content": content
                    })
            
            # Add current query
            messages.append({"role": "user", "content": query})

            model_name = "kaz-22a"

            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=self.get_available_functions(),
                tool_choice="auto",
                temperature=0.2,
                max_tokens=500
            )
            
            message = response.choices[0].message
            
            # Check if LLM wants to call a function
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                return {
                    "type": "function_call",
                    "function_name": function_name,
                    "function_args": function_args,
                    "response": message.content or f"Let me analyze that data for you."
                }
            else:
                # Pure conversational response
                return {
                    "type": "conversational", 
                    "response": message.content
                }
                
        except Exception as e:
            print(f"LLM processing error: {e}")
            print("Falling back to demo mode for this query...")
            return self._demo_function_calling_with_context(query, conversation_history or [])
    
    def _demo_function_calling_with_context(self, query: str, conversation_history: List[Dict]) -> Dict:
        """Enhanced demo mode with conversation context support"""
        query_lower = query.lower()
        
        # Extract context from conversation history
        last_function_call = None
        last_analysis_type = None
        last_drug = None
        last_region = None
        
        # Look for the most recent function call in conversation history
        for msg in reversed(conversation_history):
            if msg["role"] == "assistant" and "Function:" in msg.get("content", ""):
                # Extract function info from assistant message content
                content = msg["content"]
                if "analyze_sales_trend" in content:
                    last_analysis_type = "trend"
                    last_function_call = "analyze_sales_trend"
                elif "compare_drugs" in content:
                    last_analysis_type = "comparison"
                    last_function_call = "compare_drugs"
                elif "regional_analysis" in content:
                    last_analysis_type = "regional"
                    last_function_call = "regional_analysis"
                elif "answer_direct_question" in content:
                    last_analysis_type = "question"
                    last_function_call = "answer_direct_question"
                
                # Try to extract entities from the conversation
                if "aspirin" in content.lower():
                    last_drug = "Aspirin"
                elif "ibuprofen" in content.lower():
                    last_drug = "Ibuprofen"
                elif "medication x" in content.lower():
                    last_drug = "Medication X"
                # Add more drug extractions as needed
                
                break
        
        # Define drugs and regions for detection
        drugs = ["aspirin", "ibuprofen", "medication x", "allergy relief", 
                "blood pressure med", "diabetes control", "antibiotic plus", "vitamin d3"]
        regions = ["north america", "europe", "asia", "south america"]
        
        # Detect drug and region in current query
        detected_drug = None
        detected_region = None
        
        for drug in drugs:
            if drug in query_lower:
                detected_drug = drug.title()
                break
                
        for region in regions:
            if region in query_lower:
                detected_region = region.title()
                break
        
        # Handle explicit contextual follow-up queries
        if last_function_call and (any(phrase in query_lower for phrase in [
            "what about", "show that for", "for the same", "but for", "show me that", "do the same", "similar analysis", "same thing"
        ]) or (detected_region and any(phrase in query_lower for phrase in ["show", "that", "for"]))):
            
            # Use previous analysis type with new parameters
            if last_function_call == "analyze_sales_trend":
                return {
                    "type": "function_call",
                    "function_name": "analyze_sales_trend",
                    "function_args": {
                        "drug_name": detected_drug or last_drug,
                        "region": detected_region or last_region
                    },
                    "response": f"I'll show you the sales trend analysis{' for ' + (detected_drug or last_drug) if (detected_drug or last_drug) else ''}{' in ' + detected_region if detected_region else ''}."
                }
            elif last_function_call == "compare_drugs":
                return {
                    "type": "function_call",
                    "function_name": "compare_drugs",
                    "function_args": {"region": detected_region or last_region},
                    "response": f"I'll compare drug performance{' in ' + detected_region if detected_region else ''}."
                }
            elif last_function_call == "regional_analysis":
                return {
                    "type": "function_call",
                    "function_name": "regional_analysis",
                    "function_args": {"drug_name": detected_drug or last_drug},
                    "response": f"I'll analyze regional performance{' for ' + (detected_drug or last_drug) if (detected_drug or last_drug) else ''}."
                }
        
        # Handle standalone drug queries with context
        if detected_drug and not any(word in query_lower for word in ["hello", "hi", "thanks", "thank you"]):
            # For drug queries, default to trend analysis unless it's explicitly a direct question
            if (len(query_lower.split()) <= 3 and 
                any(phrase in query_lower for phrase in [detected_drug.lower(), "sales", "performance", "data", "info", "information", "trends", "trend"]) or
                query_lower.strip() == detected_drug.lower()):
                
                # Default to trend analysis for drug queries (this is what users typically want)
                return {
                    "type": "function_call",
                    "function_name": "analyze_sales_trend",
                    "function_args": {"drug_name": detected_drug, "region": detected_region},
                    "response": f"I'll analyze the sales trends for {detected_drug}{' in ' + detected_region if detected_region else ''}."
                }
        
        # Handle regional queries with context
        if detected_region and not detected_drug and last_function_call:
            if last_function_call == "analyze_sales_trend" and last_drug:
                return {
                    "type": "function_call",
                    "function_name": "analyze_sales_trend",
                    "function_args": {"drug_name": last_drug, "region": detected_region},
                    "response": f"I'll show you the sales trend for {last_drug} in {detected_region}."
                }
            elif last_function_call == "compare_drugs":
                return {
                    "type": "function_call", 
                    "function_name": "compare_drugs",
                    "function_args": {"region": detected_region},
                    "response": f"I'll compare drug performance in {detected_region}."
                }
        
        # Standard processing if no context match
        return self._demo_function_calling_enhanced(query)

    def _demo_function_calling_enhanced(self, query: str) -> Dict:
        """Enhanced demo function calling with better keyword detection"""
        query_lower = query.lower()
        
        # Detect drug and region
        drugs = ["aspirin", "ibuprofen", "medication x", "allergy relief", 
                "blood pressure med", "diabetes control", "antibiotic plus", "vitamin d3"]
        regions = ["north america", "europe", "asia", "south america"]
        
        detected_drug = None
        detected_region = None
        
        for drug in drugs:
            if drug in query_lower:
                detected_drug = drug.title()
                break
                
        for region in regions:
            if region in query_lower:
                detected_region = region.title()
                break
        
        # Enhanced comparison detection
        if (any(word in query_lower for word in ["compare", "comparison", "vs", "versus"]) or 
            ("all drug" in query_lower and "performance" in query_lower) or
            ("drug performance" in query_lower and "all" in query_lower) or
            ("compare all" in query_lower)):
            return {
                "type": "function_call",
                "function_name": "compare_drugs",
                "function_args": {"region": detected_region},
                "response": "I'll compare the drug performance data for you."
            }
        
        # Enhanced trend analysis detection (including drug sales queries)
        elif (detected_drug or 
              any(word in query_lower for word in ["trend", "trends", "sales", "performance"]) or
              "show me sales" in query_lower):
            return {
                "type": "function_call",
                "function_name": "analyze_sales_trend",
                "function_args": {"drug_name": detected_drug, "region": detected_region},
                "response": f"I'll analyze the sales trends{' for ' + detected_drug if detected_drug else ''}{' in ' + detected_region if detected_region else ''}."
            }
        
        # Fallback to original function
        return self._demo_function_calling(query)

class HealthcareDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('healthcare_demo.db', check_same_thread=False)
        self.init_database()
    
    def init_database(self):
        """Initialize database with sample healthcare data"""
        cursor = self.conn.cursor()
        
        # Create sales data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_name TEXT NOT NULL,
                region TEXT NOT NULL,
                sales_amount REAL NOT NULL,
                quantity_sold INTEGER NOT NULL,
                sale_date DATE NOT NULL,
                representative_id TEXT NOT NULL
            )
        ''')
        
        # Create drug information table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drug_info (
                drug_name TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                manufacturer TEXT NOT NULL,
                price_per_unit REAL NOT NULL,
                approval_date DATE
            )
        ''')
        
        # Create representatives table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS representatives (
                rep_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                region TEXT NOT NULL,
                hire_date DATE,
                performance_score REAL
            )
        ''')
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM sales_data")
        if cursor.fetchone()[0] == 0:
            self.populate_sample_data()
        
        self.conn.commit()
    
    def populate_sample_data(self):
        """Populate database with sample data"""
        cursor = self.conn.cursor()
        
        # Sample drugs
        drugs = [
            ("Aspirin", "Pain Relief", "PharmaCorp", 0.50, "2010-01-15"),
            ("Ibuprofen", "Pain Relief", "MediLab", 0.75, "2008-03-20"),
            ("Medication X", "Cardiovascular", "HeartCare Inc", 15.25, "2018-06-10"),
            ("Allergy Relief", "Antihistamine", "AllergyMed", 2.30, "2015-09-05"),
            ("Blood Pressure Med", "Cardiovascular", "CardioTech", 8.90, "2012-11-30"),
            ("Diabetes Control", "Diabetes", "DiabetesCare", 12.50, "2019-04-18"),
            ("Antibiotic Plus", "Antibiotic", "InfectControl", 6.75, "2016-08-22"),
            ("Vitamin D3", "Supplement", "NutriHealth", 1.20, "2005-02-14")
        ]
        
        cursor.executemany('''
            INSERT INTO drug_info (drug_name, category, manufacturer, price_per_unit, approval_date)
            VALUES (?, ?, ?, ?, ?)
        ''', drugs)
        
        # Sample representatives
        representatives = [
            ("REP001", "John Smith", "North America", "2020-01-15", 8.5),
            ("REP002", "Sarah Johnson", "Europe", "2019-03-20", 9.2),
            ("REP003", "Mike Chen", "Asia", "2021-06-10", 7.8),
            ("REP004", "Emily Davis", "North America", "2018-09-05", 8.9),
            ("REP005", "Carlos Rodriguez", "South America", "2020-11-30", 8.1),
            ("REP006", "Lisa Wang", "Asia", "2019-04-18", 9.0),
            ("REP007", "David Brown", "Europe", "2021-08-22", 7.5),
            ("REP008", "Anna Mueller", "Europe", "2020-02-14", 8.7)
        ]
        
        cursor.executemany('''
            INSERT INTO representatives (rep_id, name, region, hire_date, performance_score)
            VALUES (?, ?, ?, ?, ?)
        ''', representatives)
        
        # Generate sample sales data
        regions = ["North America", "Europe", "Asia", "South America"]
        drug_names = [drug[0] for drug in drugs]
        rep_ids = [rep[0] for rep in representatives]
        
        sales_data = []
        start_date = datetime.now() - timedelta(days=365)
        
        for _ in range(1000):  # Generate 1000 sales records
            drug = random.choice(drug_names)
            region = random.choice(regions)
            rep_id = random.choice([r for r in rep_ids if any(rep[2] == region for rep in representatives if rep[0] == r)])
            
            # Get drug price
            drug_price = next(d[3] for d in drugs if d[0] == drug)
            
            quantity = random.randint(10, 500)
            sales_amount = quantity * drug_price * random.uniform(0.8, 1.2)  # Add some variance
            
            sale_date = start_date + timedelta(days=random.randint(0, 365))
            
            sales_data.append((drug, region, sales_amount, quantity, sale_date.strftime('%Y-%m-%d'), rep_id))
        
        cursor.executemany('''
            INSERT INTO sales_data (drug_name, region, sales_amount, quantity_sold, sale_date, representative_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sales_data)
        
        self.conn.commit()
    
    def get_sales_data(self, drug_name=None, region=None, start_date=None, end_date=None):
        """Retrieve sales data with optional filters"""
        query = "SELECT * FROM sales_data WHERE 1=1"
        params = []
        
        if drug_name:
            query += " AND drug_name LIKE ?"
            params.append(f"%{drug_name}%")
        
        if region:
            query += " AND region = ?"
            params.append(region)
        
        if start_date:
            query += " AND sale_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND sale_date <= ?"
            params.append(end_date)
        
        return pd.read_sql_query(query, self.conn, params=params)
    
    def get_drug_info(self, drug_name=None):
        """Get drug information"""
        if drug_name:
            query = "SELECT * FROM drug_info WHERE drug_name LIKE ?"
            return pd.read_sql_query(query, self.conn, params=[f"%{drug_name}%"])
        else:
            return pd.read_sql_query("SELECT * FROM drug_info", self.conn)
    
    def get_representatives(self, region=None):
        """Get representative information"""
        if region:
            query = "SELECT * FROM representatives WHERE region = ?"
            return pd.read_sql_query(query, self.conn, params=[region])
        else:
            return pd.read_sql_query("SELECT * FROM representatives", self.conn)
    
    def get_data_summary(self):
        """Get a summary of available data for LLM context"""
        total_sales = self.get_sales_data()
        drug_info = self.get_drug_info()
        reps = self.get_representatives()
        
        return f"""
Database Summary:
- Total sales records: {len(total_sales)}
- Available drugs: {', '.join(drug_info['drug_name'].tolist())}
- Regions: {', '.join(total_sales['region'].unique())}
- Date range: {total_sales['sale_date'].min()} to {total_sales['sale_date'].max()}
- Total sales amount: ${total_sales['sales_amount'].sum():,.2f}
"""

class AnalyticsEngine:
    def __init__(self, database: HealthcareDatabase):
        self.db = database
    
    def execute_function(self, function_name: str, function_args: Dict) -> Tuple[pd.DataFrame, List, str]:
        """Execute the requested analysis function"""
        try:
            if function_name == "analyze_sales_trend":
                return self.analyze_sales_trend(function_args)
            elif function_name == "compare_drugs":
                return self.compare_drugs(function_args)
            elif function_name == "regional_analysis":
                return self.regional_analysis(function_args)
            elif function_name == "generate_auto_insights":
                return self.generate_auto_insights(function_args)
            elif function_name == "answer_direct_question":
                return self.answer_direct_question(function_args.get('question', ''), function_args)
            else:
                return pd.DataFrame(), [], f"Unknown function: {function_name}"
        except Exception as e:
            return pd.DataFrame(), [], f"Error executing {function_name}: {str(e)}"
    
    def analyze_sales_trend(self, entities: Dict) -> Tuple[pd.DataFrame, List, str]:
        """Analyze sales trends"""
        drug_name = entities.get('drug_name')
        region = entities.get('region')
        
        # Get sales data
        df = self.db.get_sales_data(drug_name=drug_name, region=region)
        
        if df.empty:
            return df, [], "No data found for the specified criteria."
        
        # Prepare data for trend analysis
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        df['month_year'] = df['sale_date'].dt.to_period('M')
        
        # Group by month and calculate totals
        monthly_sales = df.groupby('month_year').agg({
            'sales_amount': 'sum',
            'quantity_sold': 'sum'
        }).reset_index()
        
        monthly_sales['month_year_str'] = monthly_sales['month_year'].astype(str)
        
        # Create visualizations
        charts = []
        
        # Sales trend line chart
        fig1 = px.line(monthly_sales, x='month_year_str', y='sales_amount',
                      title=f'Sales Trend Over Time{f" - {drug_name}" if drug_name else ""}{f" ({region})" if region else ""}',
                      labels={'month_year_str': 'Month', 'sales_amount': 'Sales Amount ($)'})
        fig1.update_layout(xaxis_tickangle=-45)
        charts.append(fig1)
        
        # Quantity trend bar chart
        fig2 = px.bar(monthly_sales, x='month_year_str', y='quantity_sold',
                     title=f'Quantity Sold Over Time{f" - {drug_name}" if drug_name else ""}{f" ({region})" if region else ""}',
                     labels={'month_year_str': 'Month', 'quantity_sold': 'Quantity Sold'})
        fig2.update_layout(xaxis_tickangle=-45)
        charts.append(fig2)
        
        # Generate insights
        total_sales = monthly_sales['sales_amount'].sum()
        avg_monthly_sales = monthly_sales['sales_amount'].mean()
        total_quantity = monthly_sales['quantity_sold'].sum()
        
        insights = f"""
        **Sales Trend Analysis Results:**
        
        - Total Sales: ${total_sales:,.2f}
        - Average Monthly Sales: ${avg_monthly_sales:,.2f}
        - Total Quantity Sold: {total_quantity:,} units
        - Analysis Period: {len(monthly_sales)} months
        
        The data shows {"positive growth" if monthly_sales['sales_amount'].iloc[-1] > monthly_sales['sales_amount'].iloc[0] else "declining trend"} in sales over the analyzed period.
        """
        
        return monthly_sales, charts, insights
    
    def compare_drugs(self, entities: Dict) -> Tuple[pd.DataFrame, List, str]:
        """Compare drug performance"""
        region = entities.get('region')
        
        # Get sales data for all drugs
        df = self.db.get_sales_data(region=region)
        
        if df.empty:
            return df, [], "No data found for comparison."
        
        # Group by drug and calculate totals
        drug_comparison = df.groupby('drug_name').agg({
            'sales_amount': 'sum',
            'quantity_sold': 'sum'
        }).reset_index().sort_values('sales_amount', ascending=False)
        
        charts = []
        
        # Sales comparison bar chart
        fig1 = px.bar(drug_comparison, x='drug_name', y='sales_amount',
                     title=f'Drug Sales Comparison{f" ({region})" if region else ""}',
                     labels={'drug_name': 'Drug Name', 'sales_amount': 'Total Sales ($)'})
        fig1.update_layout(xaxis_tickangle=-45)
        charts.append(fig1)
        
        # Quantity comparison pie chart
        fig2 = px.pie(drug_comparison, values='quantity_sold', names='drug_name',
                     title=f'Market Share by Quantity{f" ({region})" if region else ""}')
        charts.append(fig2)
        
        # Generate insights
        top_drug = drug_comparison.iloc[0]
        insights = f"""
        **Drug Comparison Analysis:**
        
        - Top Performing Drug: {top_drug['drug_name']} (${top_drug['sales_amount']:,.2f})
        - Total Drugs Analyzed: {len(drug_comparison)}
        - Market Leader Share: {(top_drug['sales_amount'] / drug_comparison['sales_amount'].sum() * 100):.1f}% of total sales
        
        The analysis shows clear market leaders and opportunities for growth in underperforming segments.
        """
        
        return drug_comparison, charts, insights
    
    def regional_analysis(self, entities: Dict) -> Tuple[pd.DataFrame, List, str]:
        """Analyze performance by region"""
        drug_name = entities.get('drug_name')
        
        df = self.db.get_sales_data(drug_name=drug_name)
        
        if df.empty:
            return df, [], "No data found for regional analysis."
        
        # Group by region
        regional_data = df.groupby('region').agg({
            'sales_amount': 'sum',
            'quantity_sold': 'sum'
        }).reset_index().sort_values('sales_amount', ascending=False)
        
        charts = []
        
        # Regional sales bar chart
        fig1 = px.bar(regional_data, x='region', y='sales_amount',
                     title=f'Sales by Region{f" - {drug_name}" if drug_name else ""}',
                     labels={'region': 'Region', 'sales_amount': 'Total Sales ($)'})
        charts.append(fig1)
        
        # Regional market share pie chart
        fig2 = px.pie(regional_data, values='sales_amount', names='region',
                     title=f'Regional Market Share{f" - {drug_name}" if drug_name else ""}')
        charts.append(fig2)
        
        # Generate insights
        top_region = regional_data.iloc[0]
        insights = f"""
        **Regional Analysis Results:**
        
        - Top Performing Region: {top_region['region']} (${top_region['sales_amount']:,.2f})
        - Regional Distribution: {len(regional_data)} regions analyzed
        - Market Leader Share: {(top_region['sales_amount'] / regional_data['sales_amount'].sum() * 100):.1f}% of total sales
        
        This analysis helps identify key markets and expansion opportunities across different regions.
        """
        
        return regional_data, charts, insights
    
    def generate_auto_insights(self, entities: Dict) -> Tuple[pd.DataFrame, List, str]:
        """Generate automatic insights and interesting findings from the data"""
        # Get all sales data
        df = self.db.get_sales_data()
        drug_info = self.db.get_drug_info()
        
        if df.empty:
            return df, [], "No data available for analysis."
        
        charts = []
        insights = []
        
        # 1. Top performing drugs
        drug_performance = df.groupby('drug_name').agg({
            'sales_amount': 'sum',
            'quantity_sold': 'sum'
        }).reset_index().sort_values('sales_amount', ascending=False)
        
        top_drug = drug_performance.iloc[0]
        insights.append(f"**Top Performer**: {top_drug['drug_name']} leads with ${top_drug['sales_amount']:,.2f} in total sales")
        
        # 2. Regional distribution
        regional_performance = df.groupby('region')['sales_amount'].sum().sort_values(ascending=False)
        top_region = regional_performance.index[0]
        region_share = (regional_performance.iloc[0] / regional_performance.sum()) * 100
        insights.append(f"**Market Leader**: {top_region} dominates with {region_share:.1f}% of total sales")
        
        # 3. Growth trends (compare first vs last quarter)
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        df['quarter'] = df['sale_date'].dt.to_period('Q')
        quarterly_sales = df.groupby('quarter')['sales_amount'].sum()
        
        if len(quarterly_sales) >= 2:
            growth_rate = ((quarterly_sales.iloc[-1] - quarterly_sales.iloc[0]) / quarterly_sales.iloc[0]) * 100
            growth_direction = "growing" if growth_rate > 0 else "declining"
            insights.append(f"**Business Trend**: Sales are {growth_direction} with {abs(growth_rate):.1f}% change from first to last quarter")
        
        # 4. Product diversity
        category_performance = df.merge(drug_info, on='drug_name').groupby('category')['sales_amount'].sum().sort_values(ascending=False)
        top_category = category_performance.index[0]
        insights.append(f"**Product Focus**: {top_category} category generates the highest revenue")
        
        # 5. Sales concentration
        total_sales = drug_performance['sales_amount'].sum()
        top_3_share = (drug_performance.head(3)['sales_amount'].sum() / total_sales) * 100
        insights.append(f"**Market Concentration**: Top 3 drugs account for {top_3_share:.1f}% of total sales")
        
        # Create summary visualizations
        
        # Chart 1: Top 5 drugs performance
        top_5_drugs = drug_performance.head(5)
        fig1 = px.bar(top_5_drugs, x='drug_name', y='sales_amount',
                     title='Top 5 Performing Drugs',
                     labels={'drug_name': 'Drug Name', 'sales_amount': 'Total Sales ($)'},
                     color='sales_amount',
                     color_continuous_scale='viridis')
        fig1.update_layout(xaxis_tickangle=-45)
        charts.append(fig1)
        
        # Chart 2: Regional market share
        fig2 = px.pie(values=regional_performance.values, names=regional_performance.index,
                     title='Regional Market Share',
                     color_discrete_sequence=px.colors.qualitative.Set3)
        charts.append(fig2)
        
        # Chart 3: Category breakdown
        category_data = df.merge(drug_info, on='drug_name').groupby('category')['sales_amount'].sum().reset_index()
        fig3 = px.treemap(category_data, path=['category'], values='sales_amount',
                         title='Sales by Product Category')
        charts.append(fig3)
        
        # Chart 4: Monthly trend
        monthly_trend = df.groupby(df['sale_date'].dt.to_period('M'))['sales_amount'].sum().reset_index()
        monthly_trend['month'] = monthly_trend['sale_date'].astype(str)
        fig4 = px.line(monthly_trend, x='month', y='sales_amount',
                      title='Monthly Sales Trend',
                      labels={'month': 'Month', 'sales_amount': 'Sales Amount ($)'})
        fig4.update_layout(xaxis_tickangle=-45)
        charts.append(fig4)
        
        # Compile final insights
        final_insights = f"""
        **Automatic Business Insights:**
        
        {chr(10).join(insights)}
        
        **Key Metrics:**
        - Total Revenue: ${total_sales:,.2f}
        - Total Products: {len(drug_performance)} drugs across {len(category_performance)} categories
        - Market Coverage: {len(regional_performance)} regions
        - Data Period: {len(quarterly_sales)} quarters of sales data
        
        **Strategic Recommendations:**
        - Focus marketing efforts on the leading region ({top_region})
        - Consider expanding the top-performing category ({top_category})
        - Monitor the performance concentration in top products
        - Investigate opportunities in underperforming regions
        """
        
        return drug_performance, charts, final_insights
    
    def answer_direct_question(self, query: str, entities: Dict) -> Tuple[pd.DataFrame, List, str]:
        """Answer direct questions about the data with natural language responses"""
        query_lower = query.lower()
        
        # Get data for analysis
        df = self.db.get_sales_data()
        drug_info = self.db.get_drug_info()
        
        if df.empty:
            return df, [], "I don't have any sales data available to answer your question."
        
        # Question type detection and answering
        if any(phrase in query_lower for phrase in ["best seller", "top performer", "highest sales", "which is our best"]):
            # Find best selling drug
            best_drug = df.groupby('drug_name')['sales_amount'].sum().sort_values(ascending=False)
            top_drug_name = best_drug.index[0]
            top_drug_sales = best_drug.iloc[0]
            
            # Get additional info
            total_sales = df['sales_amount'].sum()
            market_share = (top_drug_sales / total_sales) * 100
            top_quantity = df[df['drug_name'] == top_drug_name]['quantity_sold'].sum()
            
            answer = f"""
            **Best Seller Analysis:**
            
            **{top_drug_name}** is our best-selling product with:
            - **${top_drug_sales:,.2f}** in total sales
            - **{market_share:.1f}%** market share
            - **{top_quantity:,}** total units sold
            
            This represents our strongest performing product across all regions and time periods.
            """
            
        elif any(phrase in query_lower for phrase in ["worst seller", "lowest sales", "poorest performer"]):
            # Find worst selling drug
            worst_drug = df.groupby('drug_name')['sales_amount'].sum().sort_values(ascending=True)
            worst_drug_name = worst_drug.index[0]
            worst_drug_sales = worst_drug.iloc[0]
            
            answer = f"""
            **Lowest Performer Analysis:**
            
            **{worst_drug_name}** has the lowest sales with:
            - **${worst_drug_sales:,.2f}** in total sales
            - This represents our biggest opportunity for improvement
            """
            
        elif any(phrase in query_lower for phrase in ["how much", "total sales", "revenue"]):
            total_sales = df['sales_amount'].sum()
            total_quantity = df['quantity_sold'].sum()
            avg_sale = df['sales_amount'].mean()
            
            answer = f"""
            **Sales Summary:**
            
            - **Total Revenue:** ${total_sales:,.2f}
            - **Total Units Sold:** {total_quantity:,}
            - **Average Sale Amount:** ${avg_sale:,.2f}
            """
            
        elif any(phrase in query_lower for phrase in ["how many", "number of"]):
            if "drugs" in query_lower or "products" in query_lower:
                drug_count = len(df['drug_name'].unique())
                answer = f"We have **{drug_count}** different drugs/products in our portfolio."
            elif "regions" in query_lower:
                region_count = len(df['region'].unique())
                regions = ', '.join(df['region'].unique())
                answer = f"We operate in **{region_count}** regions: {regions}."
            else:
                sales_count = len(df)
                answer = f"We have **{sales_count}** total sales transactions in our database."
                
        elif any(phrase in query_lower for phrase in ["which region", "best region", "top region"]):
            best_region = df.groupby('region')['sales_amount'].sum().sort_values(ascending=False)
            top_region_name = best_region.index[0]
            top_region_sales = best_region.iloc[0]
            
            answer = f"""
            **Top Performing Region:**
            
            **{top_region_name}** is our best market with:
            - **${top_region_sales:,.2f}** in total sales
            - This is our strongest geographical market
            """
            
        else:
            # Generic data lookup based on entities
            if entities.get('drug_name'):
                drug_name = entities['drug_name']
                drug_data = df[df['drug_name'].str.contains(drug_name, case=False, na=False)]
                if not drug_data.empty:
                    drug_sales = drug_data['sales_amount'].sum()
                    drug_quantity = drug_data['quantity_sold'].sum()
                    answer = f"""
                    **{drug_name} Performance:**
                    
                    - **Total Sales:** ${drug_sales:,.2f}
                    - **Units Sold:** {drug_quantity:,}
                    """
                else:
                    answer = f"I couldn't find any sales data for {drug_name}."
            else:
                answer = "I understand you're asking a question about our data. Could you be more specific? For example, ask about our best seller, total sales, or a specific drug."
        
        return pd.DataFrame(), [], answer  # Return empty DataFrame and charts list since this is text-only

def main():
    # Initialize components
    if 'db' not in st.session_state:
        st.session_state.db = HealthcareDatabase()
    
    if 'llm' not in st.session_state:
        st.session_state.llm = LLMProcessor()
    
    if 'analytics' not in st.session_state:
        st.session_state.analytics = AnalyticsEngine(st.session_state.db)
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Title and description
    st.title("Healthcare AI Assistant Demo")
    st.markdown("""
    Welcome to your intelligent healthcare assistant! I can help you with both **casual conversation** 
    and **in-depth sales data analysis**. Just ask me anything naturally.
    """)
    
    # LLM Status indicator
    if st.session_state.llm.available:
        if st.session_state.llm.demo_mode:
            st.info("AI Assistant: Enhanced Demo Mode - Intelligent conversation + data analysis!")
        else:
            st.success("AI Assistant: Full LLM Integration Active - Advanced conversation capabilities!")
    else:
        st.warning("AI Assistant: Limited Mode - Basic responses only")
    
    # Sidebar with sample queries
    with st.sidebar:
        st.header("Try These Questions")
        
        st.markdown("""
        - Show me sales trends for Aspirin
        - Compare all drug performance
        - Which is our best selling drug?
        - What's our total revenue?
        - Tell me something interesting about our business
        """)
        
        st.header("Database Info")
        total_sales = st.session_state.db.get_sales_data()
        st.metric("Total Sales Records", len(total_sales))
        st.metric("Total Drugs", len(st.session_state.db.get_drug_info()))
        st.metric("Representatives", len(st.session_state.db.get_representatives()))
    
    # Chat interface
    st.header("Chat with AI Assistant")
    
    # Display chat messages
    for message_idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "charts" in message and message["charts"]:
                cols = st.columns(len(message["charts"]))
                for i, chart in enumerate(message["charts"]):
                    with cols[i]:
                        st.plotly_chart(chart, use_container_width=True, key=f"msg_{message_idx}_chart_{i}")
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about healthcare data or just say hello..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process query with LLM-first approach
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Get data context for LLM
                data_context = st.session_state.db.get_data_summary()
                
                # Prepare conversation history for LLM (convert from our format to LLM format)
                conversation_history = []
                for msg in st.session_state.messages[:-1]:  # Exclude the current message
                    # Simplify assistant messages for context (remove technical details)
                    if msg["role"] == "assistant":
                        content = msg["content"]
                        # Extract the main response part, removing technical details
                        if "**" in content and "Analysis:" in content:
                            # For technical responses, create a simplified summary
                            parts = content.split("**")
                            if len(parts) > 1:
                                # Find the function name and main response
                                function_info = ""
                                main_response = ""
                                for i, part in enumerate(parts):
                                    if "Function:" in part:
                                        function_info = f"Function: {part.split('Function:')[1].split('\\n')[0].strip()}"
                                    elif "Args:" in part:
                                        args_info = f"Args: {part.split('Args:')[1].split('\\n')[0].strip()}"
                                        function_info += f" {args_info}"
                                    elif "Analysis Results:" in part or "Business Insights:" in part:
                                        # Extract just the summary without all details
                                        main_response = part[:200] + "..." if len(part) > 200 else part
                                        break
                                
                                simplified_content = f"{function_info}\\n{main_response}" if function_info else content[:300] + "..."
                            else:
                                simplified_content = content[:300] + "..." if len(content) > 300 else content
                        else:
                            # For conversational responses, use as-is but limit length
                            simplified_content = content[:300] + "..." if len(content) > 300 else content
                        
                        conversation_history.append({
                            "role": "assistant",
                            "content": simplified_content
                        })
                    else:
                        conversation_history.append(msg)
                
                # Process with LLM function calling
                llm_result = st.session_state.llm.process_query_with_functions(prompt, data_context, conversation_history)
                
                if llm_result.get('error'):
                    # Handle errors
                    st.error(llm_result['response'])
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": llm_result['response'],
                        "charts": []
                    })
                elif llm_result['type'] == 'conversational':
                    # Handle pure conversational responses
                    st.markdown(llm_result['response'])
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": llm_result['response'],
                        "charts": []
                    })
                elif llm_result['type'] == 'function_call':
                    # Handle function calls (data analysis)
                    try:
                        # Show initial response
                        st.markdown(llm_result['response'])
                        
                        # Execute the requested function
                        function_name = llm_result['function_name']
                        function_args = llm_result['function_args']
                        
                        data, charts, insights = st.session_state.analytics.execute_function(function_name, function_args)
                        
                        # Display results
                        st.markdown(insights)
                        
                        # Display charts with unique keys
                        if charts:
                            current_time = datetime.now().timestamp()
                            if len(charts) == 1:
                                st.plotly_chart(charts[0], use_container_width=True, key=f"chart_single_{current_time}")
                            else:
                                cols = st.columns(len(charts))
                                for i, chart in enumerate(charts):
                                    with cols[i]:
                                        st.plotly_chart(chart, use_container_width=True, key=f"chart_multi_{current_time}_{i}")
                        
                        # Create comprehensive response for message history with function details
                        full_response = f"""**Query Analysis:**
- Function: {function_name}
- Args: {function_args}

**Initial Response:** {llm_result['response']}

{insights}"""
                        
                        # Add assistant message
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": full_response,
                            "charts": charts
                        })
                        
                    except Exception as e:
                        error_message = f"I encountered an error while analyzing the data: {str(e)}"
                        st.error(error_message)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": error_message,
                            "charts": []
                        })

if __name__ == "__main__":
    main() 