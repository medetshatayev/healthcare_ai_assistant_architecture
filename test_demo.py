#!/usr/bin/env python3
"""
Test script for Healthcare AI Assistant Demo
This script tests the core components without the Streamlit interface.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database():
    """Test database initialization and data population"""
    print("🧪 Testing Database Component...")
    try:
        from demo_app import HealthcareDatabase
        db = HealthcareDatabase()
        
        # Test sales data
        sales_data = db.get_sales_data()
        print(f"  ✅ Sales records: {len(sales_data)}")
        
        # Test drug info
        drug_info = db.get_drug_info()
        print(f"  ✅ Drug records: {len(drug_info)}")
        
        # Test representatives
        reps = db.get_representatives()
        print(f"  ✅ Representative records: {len(reps)}")
        
        # Test filtered queries
        aspirin_sales = db.get_sales_data(drug_name="Aspirin")
        print(f"  ✅ Aspirin sales records: {len(aspirin_sales)}")
        
        europe_sales = db.get_sales_data(region="Europe")
        print(f"  ✅ Europe sales records: {len(europe_sales)}")
        
        return True
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False

def test_nlu():
    """Test Natural Language Understanding component"""
    print("\n🧪 Testing NLU Component...")
    try:
        from demo_app import NLUProcessor
        nlu = NLUProcessor()
        
        # Test queries
        test_queries = [
            "Show me the sales trend for Aspirin",
            "Compare drug sales performance",
            "How is Medication X performing in Europe?",
            "Give me a summary of all drug sales"
        ]
        
        for query in test_queries:
            result = nlu.process_query(query)
            print(f"  ✅ Query: '{query[:30]}...'")
            print(f"     Intent: {result['intent']}")
            print(f"     Entities: {result['entities']}")
            print(f"     Confidence: {result['confidence']:.2f}")
        
        return True
    except Exception as e:
        print(f"  ❌ NLU test failed: {e}")
        return False

def test_analytics():
    """Test Analytics Engine component"""
    print("\n🧪 Testing Analytics Component...")
    try:
        from demo_app import HealthcareDatabase, AnalyticsEngine
        
        db = HealthcareDatabase()
        analytics = AnalyticsEngine(db)
        
        # Test sales trend analysis
        print("  Testing sales trend analysis...")
        data, charts, insights = analytics.analyze_sales_trend({'drug': 'Aspirin'})
        print(f"    ✅ Generated {len(charts)} charts")
        print(f"    ✅ Insights length: {len(insights)} characters")
        
        # Test drug comparison
        print("  Testing drug comparison...")
        data, charts, insights = analytics.compare_drugs({})
        print(f"    ✅ Generated {len(charts)} charts")
        print(f"    ✅ Compared {len(data)} drugs")
        
        # Test regional analysis
        print("  Testing regional analysis...")
        data, charts, insights = analytics.regional_analysis({})
        print(f"    ✅ Generated {len(charts)} charts")
        print(f"    ✅ Analyzed {len(data)} regions")
        
        return True
    except Exception as e:
        print(f"  ❌ Analytics test failed: {e}")
        return False

def test_integration():
    """Test end-to-end integration"""
    print("\n🧪 Testing End-to-End Integration...")
    try:
        from demo_app import HealthcareDatabase, NLUProcessor, AnalyticsEngine
        
        # Initialize all components
        db = HealthcareDatabase()
        nlu = NLUProcessor()
        analytics = AnalyticsEngine(db)
        
        # Test complete workflow
        query = "Show me the sales trend for Aspirin"
        print(f"  Processing query: '{query}'")
        
        # NLU processing
        nlu_result = nlu.process_query(query)
        print(f"    Intent: {nlu_result['intent']}")
        print(f"    Entities: {nlu_result['entities']}")
        
        # Analytics processing
        if nlu_result['intent'] == 'SALES_TREND_ANALYSIS':
            data, charts, insights = analytics.analyze_sales_trend(nlu_result['entities'])
            print(f"    ✅ Generated analysis with {len(charts)} charts")
        else:
            data, charts, insights = analytics.compare_drugs(nlu_result['entities'])
            print(f"    ✅ Generated fallback analysis with {len(charts)} charts")
        
        return True
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🏥 Healthcare AI Assistant Demo - Component Tests")
    print("=" * 60)
    
    tests = [
        ("Database", test_database),
        ("NLU Processor", test_nlu),
        ("Analytics Engine", test_analytics),
        ("Integration", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The demo is ready to run.")
        print("👉 Run 'python run_demo.py' or 'streamlit run demo_app.py' to start the demo.")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 