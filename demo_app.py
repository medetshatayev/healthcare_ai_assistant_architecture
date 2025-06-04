import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import re
import os
from typing import Dict, List, Tuple, Optional

# LLM Integration
try:
    from openai import OpenAI
    from dotenv import load_dotenv
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    st.warning("⚠️ LLM packages not installed. Install with: pip install openai python-dotenv")

# Set page configuration
st.set_page_config(
    page_title="Healthcare AI Assistant Demo",
    page_icon="🏥",
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
                print("✅ LLM initialized in DEMO MODE (rule-based responses)")
                return
            
            # Get configuration from environment
            base_url = os.getenv("OPENAI_BASE_URL")
            api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                print("⚠️ No OPENAI_API_KEY found. Falling back to demo mode.")
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
                model="gpt-3.5-turbo" if not base_url else "kaz-22a",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            self.available = True
            print("✅ LLM initialized successfully with API")
            
        except Exception as e:
            print(f"⚠️ LLM API initialization failed: {e}")
            print("Falling back to demo mode...")
            self.demo_mode = True
            self.available = True
    
    def _demo_process_query(self, query: str) -> Dict:
        """Rule-based query processing for demo mode"""
        query_lower = query.lower()
        
        # Drug name detection
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
        
        # Intent detection based on keywords
        if any(word in query_lower for word in ["trend", "sales", "performance", "over time"]):
            return {
                'intent': 'SALES_TREND_ANALYSIS',
                'entities': {'drug': detected_drug, 'region': detected_region},
                'confidence': 0.8,
                'llm_response': f"I'll analyze the sales trend for {detected_drug or 'all drugs'}" + 
                              (f" in {detected_region}" if detected_region else ""),
                'needs_data_analysis': True
            }
        elif any(word in query_lower for word in ["compare", "comparison", "vs", "versus"]):
            return {
                'intent': 'COMPARATIVE_ANALYSIS',
                'entities': {'drug': detected_drug, 'region': detected_region},
                'confidence': 0.8,
                'llm_response': "I'll help you compare drug performance data.",
                'needs_data_analysis': True
            }
        elif any(word in query_lower for word in ["region", "geography", "where", "location"]):
            return {
                'intent': 'REGIONAL_ANALYSIS',
                'entities': {'drug': detected_drug, 'region': detected_region},
                'confidence': 0.8,
                'llm_response': f"I'll analyze regional performance for {detected_drug or 'drugs'}.",
                'needs_data_analysis': True
            }
        elif any(word in query_lower for word in ["summary", "overview", "general", "overall", "insights", "interesting", "findings", "what's", "tell me about"]):
            return {
                'intent': 'AUTO_INSIGHTS',
                'entities': {'drug': detected_drug, 'region': detected_region},
                'confidence': 0.8,
                'llm_response': "I'll analyze the data and show you some interesting insights about our healthcare business.",
                'needs_data_analysis': True
            }
        else:
            return {
                'intent': 'GENERAL_QUERY',
                'entities': {},
                'confidence': 0.6,
                'llm_response': "I understand you're asking about healthcare data. Could you be more specific? For example, try asking about sales trends, comparisons, or regional analysis.",
                'needs_data_analysis': False
            }
    
    def process_query(self, query: str, data_context: str = "") -> Dict:
        """Use LLM to process unclear queries"""
        if not self.available:
            return {
                'intent': 'GENERAL_QUERY',
                'entities': {},
                'confidence': 0.1,
                'llm_response': "LLM service is not available. Please check your configuration.",
                'needs_data_analysis': False
            }
        
        # Use demo mode if enabled or if API client is not available
        if self.demo_mode or self.client is None:
            return self._demo_process_query(query)
        
        try:
            # Create a prompt for the LLM to understand healthcare sales queries
            system_prompt = f"""You are a healthcare sales data analyst AI. Your job is to understand user queries about pharmaceutical sales data and help classify them.

Available data context:
{data_context}

Available drugs: Aspirin, Ibuprofen, Medication X, Allergy Relief, Blood Pressure Med, Diabetes Control, Antibiotic Plus, Vitamin D3
Available regions: North America, Europe, Asia, South America

For the user query, please:
1. Determine if this is a data analysis request (yes/no)
2. If yes, identify the intent from: SALES_TREND_ANALYSIS, COMPARATIVE_ANALYSIS, REGIONAL_ANALYSIS, SUMMARY_REQUEST
3. Extract entities like drug names, regions, time periods
4. Provide a confidence score (0-1)
5. If not a data query, provide a helpful response

Respond in JSON format:
{{
    "is_data_query": true/false,
    "intent": "intent_name",
    "entities": {{"drug": "name", "region": "name", "time_period": "period"}},
    "confidence": 0.8,
    "response": "helpful response if not a data query or explanation of what analysis will be done"
}}"""

            model_name = "gpt-3.5-turbo"
            if "pai-eas.aliyuncs.com" in str(self.client.base_url):
                model_name = "kaz-22a"

            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse LLM response
            llm_text = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                import json
                llm_result = json.loads(llm_text)
                
                return {
                    'intent': llm_result.get('intent', 'GENERAL_QUERY'),
                    'entities': llm_result.get('entities', {}),
                    'confidence': llm_result.get('confidence', 0.7),
                    'llm_response': llm_result.get('response', ''),
                    'needs_data_analysis': llm_result.get('is_data_query', False)
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as general response
                return {
                    'intent': 'GENERAL_QUERY',
                    'entities': {},
                    'confidence': 0.5,
                    'llm_response': llm_text,
                    'needs_data_analysis': False
                }
                
        except Exception as e:
            print(f"LLM processing error: {e}")
            print("Falling back to demo mode for this query...")
            return self._demo_process_query(query)

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

class NLUProcessor:
    def __init__(self, llm_processor: LLMProcessor):
        self.llm_processor = llm_processor
        self.intents = {
            'SALES_TREND_ANALYSIS': ['trend', 'sales over time', 'performance', 'growth', 'change'],
            'COMPARATIVE_ANALYSIS': ['compare', 'comparison', 'vs', 'versus', 'difference'],
            'TEMPORAL_BREAKDOWN': ['monthly', 'weekly', 'yearly', 'quarterly', 'breakdown'],
            'REGIONAL_ANALYSIS': ['region', 'country', 'area', 'geographic', 'location'],
            'DRUG_ANALYSIS': ['drug', 'medication', 'medicine', 'pharmaceutical'],
            'VISUALIZATION_REQUEST': ['chart', 'graph', 'plot', 'visualize', 'show'],
            'AUTO_INSIGHTS': ['insights', 'interesting', 'findings', 'summary', 'overview', 'report', 'tell me about', 'what', 'general', 'overall', 'business']
        }
        
        self.entities = {
            'drugs': ['aspirin', 'ibuprofen', 'medication x', 'allergy relief', 
                     'blood pressure med', 'diabetes control', 'antibiotic plus', 'vitamin d3'],
            'regions': ['north america', 'europe', 'asia', 'south america'],
            'time_periods': ['week', 'month', 'quarter', 'year', 'last 3 months', 'last 6 months'],
            'chart_types': ['bar', 'line', 'pie', 'scatter']
        }
    
    def process_query(self, query: str, data_context: str = "") -> Dict:
        """Process user query to extract intent and entities with LLM fallback"""
        query_lower = query.lower()
        
        # First try rule-based approach
        detected_intent = 'GENERAL_QUERY'
        max_matches = 0
        
        for intent, keywords in self.intents.items():
            matches = sum(1 for keyword in keywords if keyword in query_lower)
            if matches > max_matches:
                max_matches = matches
                detected_intent = intent
        
        # Entity extraction
        entities = {}
        
        # Extract drugs
        for drug in self.entities['drugs']:
            if drug in query_lower:
                entities['drug'] = drug.title()
                break
        
        # Extract regions
        for region in self.entities['regions']:
            if region in query_lower:
                entities['region'] = region.title()
                break
        
        # Extract time periods
        for period in self.entities['time_periods']:
            if period in query_lower:
                entities['time_period'] = period
                break
        
        # Extract chart types
        for chart_type in self.entities['chart_types']:
            if chart_type in query_lower:
                entities['chart_type'] = chart_type
                break
        
        confidence = min(max_matches / 3, 1.0)  # Normalize confidence
        
        # If confidence is low, try LLM
        if confidence < 0.3 or detected_intent == 'GENERAL_QUERY':
            llm_result = self.llm_processor.process_query(query, data_context)
            
            # If LLM indicates it's a data query with higher confidence, use LLM result
            if llm_result['needs_data_analysis'] and llm_result['confidence'] > confidence:
                return {
                    'intent': llm_result['intent'],
                    'entities': llm_result['entities'],
                    'confidence': llm_result['confidence'],
                    'source': 'LLM',
                    'llm_response': llm_result['llm_response']
                }
            elif not llm_result['needs_data_analysis']:
                # For non-data queries, return LLM response directly
                return {
                    'intent': 'GENERAL_QUERY',
                    'entities': {},
                    'confidence': llm_result['confidence'],
                    'source': 'LLM',
                    'llm_response': llm_result['llm_response']
                }
        
        # Return rule-based result
        return {
            'intent': detected_intent,
            'entities': entities,
            'confidence': confidence,
            'source': 'Rule-based',
            'llm_response': None
        }

class AnalyticsEngine:
    def __init__(self, database: HealthcareDatabase):
        self.db = database
    
    def analyze_sales_trend(self, entities: Dict) -> Tuple[pd.DataFrame, List, str]:
        """Analyze sales trends"""
        drug_name = entities.get('drug')
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
        
        • Total Sales: ${total_sales:,.2f}
        • Average Monthly Sales: ${avg_monthly_sales:,.2f}
        • Total Quantity Sold: {total_quantity:,} units
        • Analysis Period: {len(monthly_sales)} months
        
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
        
        • Top Performing Drug: {top_drug['drug_name']} (${top_drug['sales_amount']:,.2f})
        • Total Drugs Analyzed: {len(drug_comparison)}
        • Market Leader Share: {(top_drug['sales_amount'] / drug_comparison['sales_amount'].sum() * 100):.1f}% of total sales
        
        The analysis shows clear market leaders and opportunities for growth in underperforming segments.
        """
        
        return drug_comparison, charts, insights
    
    def regional_analysis(self, entities: Dict) -> Tuple[pd.DataFrame, List, str]:
        """Analyze performance by region"""
        drug_name = entities.get('drug')
        
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
        
        • Top Performing Region: {top_region['region']} (${top_region['sales_amount']:,.2f})
        • Regional Distribution: {len(regional_data)} regions analyzed
        • Market Leader Share: {(top_region['sales_amount'] / regional_data['sales_amount'].sum() * 100):.1f}% of total sales
        
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
        insights.append(f"🏆 **Top Performer**: {top_drug['drug_name']} leads with ${top_drug['sales_amount']:,.2f} in total sales")
        
        # 2. Regional distribution
        regional_performance = df.groupby('region')['sales_amount'].sum().sort_values(ascending=False)
        top_region = regional_performance.index[0]
        region_share = (regional_performance.iloc[0] / regional_performance.sum()) * 100
        insights.append(f"🌍 **Market Leader**: {top_region} dominates with {region_share:.1f}% of total sales")
        
        # 3. Growth trends (compare first vs last quarter)
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        df['quarter'] = df['sale_date'].dt.to_period('Q')
        quarterly_sales = df.groupby('quarter')['sales_amount'].sum()
        
        if len(quarterly_sales) >= 2:
            growth_rate = ((quarterly_sales.iloc[-1] - quarterly_sales.iloc[0]) / quarterly_sales.iloc[0]) * 100
            growth_direction = "📈 growing" if growth_rate > 0 else "📉 declining"
            insights.append(f"📊 **Business Trend**: Sales are {growth_direction} with {abs(growth_rate):.1f}% change from first to last quarter")
        
        # 4. Product diversity
        category_performance = df.merge(drug_info, on='drug_name').groupby('category')['sales_amount'].sum().sort_values(ascending=False)
        top_category = category_performance.index[0]
        insights.append(f"💊 **Product Focus**: {top_category} category generates the highest revenue")
        
        # 5. Sales concentration
        total_sales = drug_performance['sales_amount'].sum()
        top_3_share = (drug_performance.head(3)['sales_amount'].sum() / total_sales) * 100
        insights.append(f"🎯 **Market Concentration**: Top 3 drugs account for {top_3_share:.1f}% of total sales")
        
        # Create summary visualizations
        
        # Chart 1: Top 5 drugs performance
        top_5_drugs = drug_performance.head(5)
        fig1 = px.bar(top_5_drugs, x='drug_name', y='sales_amount',
                     title='🏆 Top 5 Performing Drugs',
                     labels={'drug_name': 'Drug Name', 'sales_amount': 'Total Sales ($)'},
                     color='sales_amount',
                     color_continuous_scale='viridis')
        fig1.update_layout(xaxis_tickangle=-45)
        charts.append(fig1)
        
        # Chart 2: Regional market share
        fig2 = px.pie(values=regional_performance.values, names=regional_performance.index,
                     title='🌍 Regional Market Share',
                     color_discrete_sequence=px.colors.qualitative.Set3)
        charts.append(fig2)
        
        # Chart 3: Category breakdown
        category_data = df.merge(drug_info, on='drug_name').groupby('category')['sales_amount'].sum().reset_index()
        fig3 = px.treemap(category_data, path=['category'], values='sales_amount',
                         title='💊 Sales by Product Category')
        charts.append(fig3)
        
        # Chart 4: Monthly trend
        monthly_trend = df.groupby(df['sale_date'].dt.to_period('M'))['sales_amount'].sum().reset_index()
        monthly_trend['month'] = monthly_trend['sale_date'].astype(str)
        fig4 = px.line(monthly_trend, x='month', y='sales_amount',
                      title='📊 Monthly Sales Trend',
                      labels={'month': 'Month', 'sales_amount': 'Sales Amount ($)'})
        fig4.update_layout(xaxis_tickangle=-45)
        charts.append(fig4)
        
        # Compile final insights
        final_insights = f"""
        **🔍 Automatic Business Insights:**
        
        {chr(10).join(insights)}
        
        **📈 Key Metrics:**
        • Total Revenue: ${total_sales:,.2f}
        • Total Products: {len(drug_performance)} drugs across {len(category_performance)} categories
        • Market Coverage: {len(regional_performance)} regions
        • Data Period: {len(quarterly_sales)} quarters of sales data
        
        **💡 Strategic Recommendations:**
        • Focus marketing efforts on the leading region ({top_region})
        • Consider expanding the top-performing category ({top_category})
        • Monitor the performance concentration in top products
        • Investigate opportunities in underperforming regions
        """
        
        return drug_performance, charts, final_insights

def main():
    # Initialize components
    if 'db' not in st.session_state:
        st.session_state.db = HealthcareDatabase()
    
    if 'llm' not in st.session_state:
        st.session_state.llm = LLMProcessor()
    
    if 'nlu' not in st.session_state:
        st.session_state.nlu = NLUProcessor(st.session_state.llm)
    
    if 'analytics' not in st.session_state:
        st.session_state.analytics = AnalyticsEngine(st.session_state.db)
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Title and description
    st.title("🏥 Healthcare AI Assistant Demo")
    st.markdown("""
    This demo showcases an AI-powered healthcare assistant that can analyze sales data, 
    generate insights, and create visualizations based on natural language queries.
    """)
    
    # LLM Status indicator
    if st.session_state.llm.available:
        st.success("🤖 LLM Integration: Active - Can handle complex queries!")
    else:
        st.warning("⚠️ LLM Integration: Offline - Using keyword-based matching only")
    
    # Sidebar with sample queries
    with st.sidebar:
        st.header("📊 Sample Queries")
        
        if st.session_state.llm.available:
            st.markdown("""
            **With LLM Enhanced Understanding:**
            
            **Sales Trends:**
            - "Show me the sales trend for Aspirin"
            - "How has our cardiovascular medication performed?"
            - "What's happening with pain relief drugs?"
            
            **Comparisons:**
            - "Which is our best seller?"
            - "Compare all our heart medications"
            - "Show me drug performance rankings"
            
            **Regional Analysis:**
            - "How are we doing in different markets?"
            - "Where does Aspirin sell best?"
            - "Regional breakdown please"
            
            **General Questions:**
            - "Tell me about our business"
            - "What should I know about our sales?"
            - "Any interesting insights?"
            - "Hello, how can you help?"
            """)
        else:
            st.markdown("""
            Try these example queries:
            
            **Sales Trends:**
            - "Show me the sales trend for Aspirin"
            - "How has Medication X performed over time?"
            
            **Comparisons:**
            - "Compare drug sales performance"
            - "Which drugs sell best in Europe?"
            
            **Regional Analysis:**
            - "Show sales by region"
            - "How is Aspirin performing in North America?"
            
            **General Questions:**
            - "Give me a summary of all drug sales"
            - "What are the top performing medications?"
            """)
        
        st.header("🗃️ Database Info")
        total_sales = st.session_state.db.get_sales_data()
        st.metric("Total Sales Records", len(total_sales))
        st.metric("Total Drugs", len(st.session_state.db.get_drug_info()))
        st.metric("Representatives", len(st.session_state.db.get_representatives()))
        
        if st.session_state.llm.available:
            st.header("🤖 LLM Status")
            st.success("Connected to kaz-22a model")
            if st.button("Test LLM Connection"):
                test_result = st.session_state.llm.process_query("Hello, are you working?", "")
                if test_result['llm_response']:
                    st.write("✅ LLM Response:", test_result['llm_response'][:100] + "...")
                else:
                    st.error("❌ LLM not responding")
    
    # Chat interface
    st.header("💬 Chat with AI Assistant")
    
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
    if prompt := st.chat_input("Ask me about healthcare sales data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your query..."):
                # Get data context for LLM
                data_context = st.session_state.db.get_data_summary()
                
                # NLU processing
                nlu_result = st.session_state.nlu.process_query(prompt, data_context)
                
                # Check if this is a general query handled by LLM
                if nlu_result.get('llm_response') and nlu_result['intent'] == 'GENERAL_QUERY':
                    # Handle general questions with LLM response
                    response = f"""
                    **Query Processing:**
                    - Source: {nlu_result.get('source', 'Unknown')}
                    - Confidence: {nlu_result['confidence']:.2f}
                    
                    **Response:**
                    {nlu_result['llm_response']}
                    """
                    
                    st.markdown(response)
                    
                    # Add assistant message
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "charts": []
                    })
                else:
                    # Handle data analysis queries
                    intent = nlu_result['intent']
                    entities = nlu_result['entities']
                    charts = []
                    
                    try:
                        if intent == 'SALES_TREND_ANALYSIS':
                            data, charts, insights = st.session_state.analytics.analyze_sales_trend(entities)
                        elif intent == 'COMPARATIVE_ANALYSIS':
                            data, charts, insights = st.session_state.analytics.compare_drugs(entities)
                        elif intent == 'REGIONAL_ANALYSIS':
                            data, charts, insights = st.session_state.analytics.regional_analysis(entities)
                        elif intent == 'AUTO_INSIGHTS':
                            data, charts, insights = st.session_state.analytics.generate_auto_insights(entities)
                        else:
                            # Default: show general summary
                            data, charts, insights = st.session_state.analytics.compare_drugs(entities)
                        
                        # Display response
                        response = f"""
                        **Query Analysis:**
                        - Intent: {intent.replace('_', ' ').title()}
                        - Source: {nlu_result.get('source', 'Rule-based')}
                        - Confidence: {nlu_result['confidence']:.2f}
                        - Entities: {', '.join([f"{k}: {v}" for k, v in entities.items()]) if entities else 'None detected'}
                        
                        {insights}
                        """
                        
                        if nlu_result.get('llm_response'):
                            response += f"\n\n**AI Insight:** {nlu_result['llm_response']}"
                        
                        st.markdown(response)
                        
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
                        
                        # Add assistant message
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response,
                            "charts": charts
                        })
                        
                    except Exception as e:
                        error_message = f"I encountered an error processing your query: {str(e)}"
                        st.error(error_message)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": error_message,
                            "charts": []
                        })

if __name__ == "__main__":
    main() 