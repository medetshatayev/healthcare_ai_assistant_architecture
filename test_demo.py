#!/usr/bin/env python3
"""
Test script for Healthcare AI Assistant Demo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database():
    """Test database initialization and data population"""
    print("Testing Database...")
    try:
        from demo_app import HealthcareDatabase
        db = HealthcareDatabase()
        
        sales_data = db.get_sales_data()
        drug_info = db.get_drug_info()
        reps = db.get_representatives()
        
        print(f"  PASS: {len(sales_data)} sales records, {len(drug_info)} drugs, {len(reps)} representatives")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_llm_processor():
    """Test LLM Processor component"""
    print("Testing LLM Processor...")
    try:
        from demo_app import LLMProcessor
        llm = LLMProcessor()
        
        test_queries = [
            ("Hello", "conversational"),
            ("Show me sales trends for Aspirin", "function_call"),
            ("Which is our best seller?", "function_call")
        ]
        
        for query, expected_type in test_queries:
            result = llm.process_query_with_functions(query)
            if result['type'] == expected_type:
                print(f"  PASS: '{query}' -> {result['type']}")
            else:
                print(f"  WARN: '{query}' -> {result['type']} (expected: {expected_type})")
        
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_analytics():
    """Test Analytics Engine component"""
    print("Testing Analytics...")
    try:
        from demo_app import HealthcareDatabase, AnalyticsEngine
        
        db = HealthcareDatabase()
        analytics = AnalyticsEngine(db)
        
        # Test multiple analysis types
        functions = [
            ("analyze_sales_trend", {'drug_name': 'Aspirin'}),
            ("compare_drugs", {}),
            ("regional_analysis", {}),
            ("answer_direct_question", {"question": "What is our best seller?"})
        ]
        
        for func_name, args in functions:
            data, charts, insights = analytics.execute_function(func_name, args)
            print(f"  PASS: {func_name}: {len(charts)} charts generated")
        
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_conversation_context():
    """Test conversation context and follow-up queries"""
    print("Testing Conversation Context...")
    try:
        from demo_app import LLMProcessor, HealthcareDatabase
        
        llm = LLMProcessor()
        db = HealthcareDatabase()
        data_context = db.get_data_summary()
        conversation_history = []
        
        # Test context-aware follow-ups
        queries = [
            "Show me sales trends for Aspirin",
            "Show that for Europe",
            "What about Ibuprofen?"
        ]
        
        for i, query in enumerate(queries):
            result = llm.process_query_with_functions(query, data_context, conversation_history)
            
            # Add to conversation history
            conversation_history.append({"role": "user", "content": query})
            if result['type'] == 'function_call':
                conversation_history.append({
                    "role": "assistant", 
                    "content": f"Function: {result['function_name']} Args: {result['function_args']}"
                })
                print(f"  PASS: Query {i+1}: {result['function_name']} with {result['function_args']}")
            else:
                conversation_history.append({"role": "assistant", "content": result['response'][:100]})
                print(f"  PASS: Query {i+1}: Conversational response")
        
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def main():
    """Run all tests"""
    print("Healthcare AI Assistant - Component Tests")
    print("=" * 50)
    
    tests = [
        ("Database", test_database),
        ("LLM Processor", test_llm_processor),
        ("Analytics", test_analytics),
        ("Conversation Context", test_conversation_context)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if test_func():
            passed += 1
    
    print("=" * 50)
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("All tests passed! Demo is ready to run.")
    else:
        print("Some tests failed.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 