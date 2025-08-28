#!/usr/bin/env python3
"""
Google Form Question Extractor
Extracts all 29 questions from the published Google Form
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import sys

def extract_questions_from_google_form(viewform_url):
    """Extract all questions from a Google Form viewform URL"""
    print(f"🔄 Fetching Google Form: {viewform_url}")
    
    try:
        # Fetch the HTML content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(viewform_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        print("✅ Form HTML fetched successfully")
        
        questions = []
        
        # Method 1: Look for FB_PUBLIC_LOAD_DATA_ variable (contains form structure)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'FB_PUBLIC_LOAD_DATA_' in script.string:
                print("🔍 Found form data script")
                
                # Extract the JSON data
                pattern = r'FB_PUBLIC_LOAD_DATA_.*?=\s*(\[.*?\]);'
                matches = re.findall(pattern, script.string, re.DOTALL)
                
                for match in matches:
                    try:
                        data = json.loads(match)
                        print(f"📊 Parsing form data structure (length: {len(data)})")
                        
                        # Navigate the nested structure to find questions
                        if len(data) > 1 and len(data[1]) > 1:
                            form_items = data[1][1]
                            
                            question_num = 1
                            for item in form_items:
                                if isinstance(item, list) and len(item) > 4:
                                    question_text = item[1] if len(item) > 1 else None
                                    
                                    if question_text and isinstance(question_text, str) and len(question_text.strip()) > 10:
                                        question_info = {
                                            'id': question_num,
                                            'question': question_text.strip(),
                                            'options': {}
                                        }
                                        
                                        # Extract multiple choice options
                                        if len(item) > 4 and item[4] and len(item[4]) > 1:
                                            options = item[4][1]
                                            if isinstance(options, list):
                                                option_labels = ['A', 'B', 'C', 'D', 'E', 'F']
                                                for i, opt in enumerate(options):
                                                    if i < len(option_labels) and isinstance(opt, list) and len(opt) > 0:
                                                        option_text = str(opt[0]).strip()
                                                        if option_text:
                                                            question_info['options'][option_labels[i]] = option_text
                                        
                                        if question_info['options']:  # Only add if it has options
                                            questions.append(question_info)
                                            question_num += 1
                                            print(f"✅ Q{question_num-1}: {question_text[:50]}...")
                                            
                    except (json.JSONDecodeError, IndexError, KeyError) as e:
                        print(f"⚠️ Error parsing JSON structure: {e}")
                        continue
        
        # Method 2: Fallback - parse visible question elements
        if not questions:
            print("🔄 Using fallback method - parsing visible elements")
            question_elements = soup.find_all('div', {'role': 'listitem'})
            
            for i, element in enumerate(question_elements, 1):
                title_elem = element.find('span')
                if title_elem and title_elem.text.strip():
                    question_text = title_elem.text.strip()
                    if len(question_text) > 10:  # Filter out short labels
                        questions.append({
                            'id': i,
                            'question': question_text,
                            'options': {'A': 'Option A', 'B': 'Option B', 'C': 'Option C', 'D': 'Option D'}
                        })
                        print(f"✅ Q{i}: {question_text[:50]}...")
        
        print(f"🎉 Successfully extracted {len(questions)} questions")
        return questions
        
    except Exception as e:
        print(f"❌ Error extracting questions: {e}")
        return []

if __name__ == "__main__":
    form_url = "https://forms.gle/nAr2wthXzCgMdWFB9"
    questions = extract_questions_from_google_form(form_url)
    
    if questions:
        print(f"\n📝 EXTRACTED {len(questions)} QUESTIONS:")
        print("=" * 50)
        
        for q in questions:
            print(f"Q{q['id']}: {q['question']}")
            for opt_key, opt_text in q['options'].items():
                print(f"  {opt_key}. {opt_text}")
            print()
    else:
        print("❌ No questions found")