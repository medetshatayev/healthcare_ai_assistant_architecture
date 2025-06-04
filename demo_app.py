import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import re
from typing import Dict, List, Tuple, Optional

# Set page configuration
st.set_page_config(
    page_title="Healthcare AI Assistant Demo",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

class NLUProcessor:
    def __init__(self):
        self.intents = {
            'SALES_TREND_ANALYSIS': ['trend', 'sales over time', 'performance', 'growth', 'change'],
            'COMPARATIVE_ANALYSIS': ['compare', 'comparison', 'vs', 'versus', 'difference'],
            'TEMPORAL_BREAKDOWN': ['monthly', 'weekly', 'yearly', 'quarterly', 'breakdown'],
            'REGIONAL_ANALYSIS': ['region', 'country', 'area', 'geographic', 'location'],
            'DRUG_ANALYSIS': ['drug', 'medication', 'medicine', 'pharmaceutical'],
            'VISUALIZATION_REQUEST': ['chart', 'graph', 'plot', 'visualize', 'show'],
            'SUMMARY_REQUEST': ['summary', 'overview', 'report', 'total', 'aggregate']
        }
        
        self.entities = {
            'drugs': ['aspirin', 'ibuprofen', 'medication x', 'allergy relief', 
                     'blood pressure med', 'diabetes control', 'antibiotic plus', 'vitamin d3'],
            'regions': ['north america', 'europe', 'asia', 'south america'],
            'time_periods': ['week', 'month', 'quarter', 'year', 'last 3 months', 'last 6 months'],
            'chart_types': ['bar', 'line', 'pie', 'scatter']
        }
    
    def process_query(self, query: str) -> Dict:
        """Process user query to extract intent and entities"""
        query_lower = query.lower()
        
        # Intent classification
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
        
        return {
            'intent': detected_intent,
            'entities': entities,
            'confidence': min(max_matches / 3, 1.0)  # Normalize confidence
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

def main():
    # Initialize components
    if 'db' not in st.session_state:
        st.session_state.db = HealthcareDatabase()
    
    if 'nlu' not in st.session_state:
        st.session_state.nlu = NLUProcessor()
    
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
    
    # Sidebar with sample queries
    with st.sidebar:
        st.header("📊 Sample Queries")
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
    
    # Chat interface
    st.header("💬 Chat with AI Assistant")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "charts" in message and message["charts"]:
                cols = st.columns(len(message["charts"]))
                for i, chart in enumerate(message["charts"]):
                    with cols[i]:
                        st.plotly_chart(chart, use_container_width=True)
    
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
                # NLU processing
                nlu_result = st.session_state.nlu.process_query(prompt)
                
                # Generate response based on intent
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
                    else:
                        # Default: show general summary
                        data, charts, insights = st.session_state.analytics.compare_drugs(entities)
                    
                    # Display response
                    response = f"""
                    **Query Analysis:**
                    - Intent: {intent.replace('_', ' ').title()}
                    - Confidence: {nlu_result['confidence']:.2f}
                    - Entities: {', '.join([f"{k}: {v}" for k, v in entities.items()]) if entities else 'None detected'}
                    
                    {insights}
                    """
                    
                    st.markdown(response)
                    
                    # Display charts
                    if charts:
                        if len(charts) == 1:
                            st.plotly_chart(charts[0], use_container_width=True)
                        else:
                            cols = st.columns(len(charts))
                            for i, chart in enumerate(charts):
                                with cols[i]:
                                    st.plotly_chart(chart, use_container_width=True)
                    
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