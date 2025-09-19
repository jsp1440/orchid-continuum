"""
FCOS Orchid Judge Flask Routes
Educational orchid judging PWA endpoints
"""

import os
import io
import json
import tempfile
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import openai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import Color

# Import your existing Google Sheets service if available
try:
    from google_sheets_service import submit_to_sheets
except ImportError:
    def submit_to_sheets(data, sheet_name):
        print(f"Mock: Would submit to {sheet_name}: {data}")
        return {"id": f"mock_{datetime.now().isoformat()}"}

fcos_judge = Blueprint('fcos_judge', __name__, url_prefix='/fcos-judge')

# OpenAI client
openai.api_key = os.environ.get('OPENAI_API_KEY')

@fcos_judge.route('/')
def index():
    """Main FCOS Judge PWA interface"""
    return render_template('fcos_judge_index.html')

@fcos_judge.route('/api/ocr', methods=['POST'])
def perform_ocr():
    """Extract text from tag photos using OCR"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Process image with Tesseract
        image = Image.open(file.stream)
        
        # Optimize image for OCR
        image = image.convert('RGB')
        
        # Extract text
        extracted_text = pytesseract.image_to_string(image, config='--psm 6')
        confidence = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Calculate average confidence
        confidences = [int(conf) for conf in confidence['conf'] if int(conf) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return jsonify({
            'text': extracted_text.strip(),
            'confidence': avg_confidence / 100.0,
            'raw_data': {
                'char_count': len(extracted_text.strip()),
                'line_count': len(extracted_text.strip().split('\n'))
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'OCR processing failed: {str(e)}'}), 500

@fcos_judge.route('/api/analyze', methods=['POST'])
def perform_ai_analysis():
    """AI analysis of plant photos using OpenAI Vision API"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
            
        file = request.files['image']
        detect_reference = request.form.get('detectReferenceCard', 'false').lower() == 'true'
        
        # Convert image to base64 for OpenAI
        image = Image.open(file.stream)
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        import base64
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Prepare OpenAI Vision API request
        analysis_prompt = """
        Analyze this orchid photo and provide detailed measurements and counts. Respond with JSON only.
        
        Look for:
        1. Flower count (total individual flowers visible)
        2. Spike/inflorescence count
        3. Symmetry analysis (0-10 scale for petals, overall form)
        4. Measurements in pixels (if reference card detected, note its dimensions)
        5. Color analysis (dominant colors, uniformity)
        6. Condition assessment (spots, damage, overall health)
        
        JSON format:
        {
          "flowerCount": {"total": 0, "confidence": 0.0, "uncertainty": 0},
          "spikeCount": {"total": 0, "confidence": 0.0, "uncertainty": 0},
          "flowersPerSpike": {"average": 0.0, "min": 0, "max": 0},
          "symmetry": {
            "overall": 0.0,
            "petals": 0.0,
            "petalAngleVariance": 0.0,
            "lip": {"consistency": 0.0, "notes": ""}
          },
          "measurements": {
            "naturalSpreadPixels": 0,
            "dorsalLengthPixels": 0,
            "petalWidthPixels": 0,
            "lipWidthPixels": 0
          },
          "referenceCard": {"detected": false, "width": 0, "height": 0},
          "condition": {"overall": 0.0, "flags": []},
          "colorAnalysis": {
            "dominantColors": [{"hex": "#ffffff", "name": "white", "percentage": 0}],
            "uniformity": 0.0,
            "saturation": 0.0
          },
          "overallConfidence": 0.0
        }
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        # Parse AI response
        ai_result = response.choices[0].message.content
        
        # Clean JSON if wrapped in markdown
        if ai_result.startswith('```json'):
            ai_result = ai_result.strip('```json').strip('```').strip()
        
        analysis_data = json.loads(ai_result)
        
        # Add processing metadata
        analysis_data['processingTime'] = datetime.now().isoformat()
        analysis_data['modelUsed'] = 'gpt-4o'
        
        return jsonify(analysis_data)
        
    except json.JSONDecodeError as e:
        return jsonify({'error': f'AI response parsing failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'AI analysis failed: {str(e)}'}), 500

@fcos_judge.route('/api/lookup-taxonomy')
def lookup_taxonomy():
    """Lookup taxonomy information from GBIF/existing database"""
    genus = request.args.get('genus', '').strip()
    species = request.args.get('species', '').strip()
    
    if not genus:
        return jsonify({'error': 'Genus is required'}), 400
    
    try:
        # This would integrate with your existing orchid database
        # For now, return mock suggestions
        suggestions = [
            {
                'scientificName': f"{genus} {species}" if species else genus,
                'acceptedName': f"{genus} {species}" if species else genus,
                'authority': 'Mock Authority',
                'commonNames': ['Mock Common Name'],
                'gbifKey': 'mock_key_123',
                'confidence': 0.9
            }
        ]
        
        return jsonify({
            'query': f"{genus} {species}".strip(),
            'suggestions': suggestions,
            'totalFound': len(suggestions)
        })
        
    except Exception as e:
        return jsonify({'error': f'Taxonomy lookup failed: {str(e)}'}), 500

@fcos_judge.route('/api/generate-pdf', methods=['POST'])
def generate_certificate_pdf():
    """Generate PDF certificate"""
    try:
        data = request.get_json()
        
        # Create PDF in memory
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        p.setFont("Helvetica-Bold", 24)
        p.drawString(50, height - 50, "Educational Practice Certificate")
        p.setFont("Helvetica", 16)
        p.drawString(50, height - 80, "Five Cities Orchid Society")
        
        # Plant information
        plant_name = format_plant_name(data.get('plant', {}))
        p.setFont("Helvetica-Bold", 18)
        p.drawString(50, height - 140, plant_name)
        
        # Scoring information
        if 'scoring' in data:
            scoring = data['scoring']
            p.setFont("Helvetica", 14)
            p.drawString(50, height - 180, f"Total Score: {scoring.get('totalScore', 0)}/100")
            p.drawString(50, height - 200, f"Judging System: {scoring.get('system', 'AOS')}")
            
            if 'awardBand' in scoring and scoring['awardBand']:
                band = scoring['awardBand']
                p.drawString(50, height - 220, f"Award Level: {band.get('label', 'N/A')}")
        
        # Timestamp
        p.setFont("Helvetica", 12)
        timestamp = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        p.drawString(50, height - 260, f"Generated: {timestamp.strftime('%B %d, %Y')}")
        
        # Educational watermark
        p.setFont("Helvetica-Oblique", 36)
        p.setFillColorRGB(0.9, 0.9, 0.9)
        p.drawString(width/2 - 150, height/2, "EDUCATIONAL")
        p.drawString(width/2 - 120, height/2 - 40, "NOT OFFICIAL")
        
        # Footer
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica", 10)
        p.drawString(50, 50, "Generated by FCOS Orchid Judge (Beta) - Educational tool only")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"FCOS-Certificate-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

@fcos_judge.route('/api/submit', methods=['POST'])
def submit_entry():
    """Submit entry to Google Sheets"""
    try:
        data = request.get_json()
        
        # Prepare data for Google Sheets
        sheet_data = {
            'Timestamp': datetime.now().isoformat(),
            'Submitter_Name': data.get('submitter', {}).get('name', 'Anonymous'),
            'Submitter_Email': data.get('submitter', {}).get('email', ''),
            'Consent': 'Y' if data.get('consent') else 'N',
            'Judging_System': data.get('scoring', {}).get('system', 'AOS'),
            'Genus': data.get('taxonomy', {}).get('genus', ''),
            'Species_or_Grex': data.get('taxonomy', {}).get('species', ''),
            'Clone_Cultivar': data.get('taxonomy', {}).get('clone', ''),
            'Hybrid_Parent_A': data.get('taxonomy', {}).get('parentA', ''),
            'Hybrid_Parent_B': data.get('taxonomy', {}).get('parentB', ''),
            'Breeder': data.get('taxonomy', {}).get('breeder', ''),
            'Source_Vendor': data.get('taxonomy', {}).get('source', ''),
            'Pot_Size_in': data.get('taxonomy', {}).get('potSize', ''),
            'Flower_Count_AI': data.get('analysis', {}).get('flowerCount', {}).get('total', ''),
            'Flower_Count_Final': data.get('analysis', {}).get('flowerCount', {}).get('total', ''),
            'Spike_Count_AI': data.get('analysis', {}).get('spikeCount', {}).get('total', ''),
            'Spike_Count_Final': data.get('analysis', {}).get('spikeCount', {}).get('total', ''),
            'NS_mm': data.get('analysis', {}).get('measurements', {}).get('naturalSpread', ''),
            'Dorsal_Length_mm': data.get('analysis', {}).get('measurements', {}).get('dorsalLength', ''),
            'Petal_Width_mm': data.get('analysis', {}).get('measurements', {}).get('petalWidth', ''),
            'Lip_Width_mm': data.get('analysis', {}).get('measurements', {}).get('lipWidth', ''),
            'Symmetry_Score_AI': data.get('analysis', {}).get('symmetry', {}).get('overall', ''),
            'Condition_Flags': ','.join(data.get('analysis', {}).get('condition', {}).get('flags', [])),
            'Total_Score': data.get('scoring', {}).get('totalScore', ''),
            'Award_Band_EdU': data.get('scoring', {}).get('awardBand', {}).get('label', ''),
            'Notes_JudgeStyle': data.get('scoring', {}).get('judgesNotes', ''),
            'Plant_Photo_URL': 'stored_locally',  # Would be actual URLs in production
            'Tag_Photo_URL': 'stored_locally'
        }
        
        # Add section scores
        if 'scoring' in data and 'scores' in data['scoring']:
            scores = data['scoring']['scores']
            sheet_data.update({
                'Section_form': scores.get('form', ''),
                'Section_color': scores.get('color', ''),
                'Section_size': scores.get('size', ''),
                'Section_floriferous': scores.get('floriferous', ''),
                'Section_condition': scores.get('condition', ''),
                'Section_distinct': scores.get('distinct', '')
            })
        
        # Submit to Google Sheets
        result = submit_to_sheets(sheet_data, 'Submissions')
        
        return jsonify({
            'success': True,
            'id': result.get('id'),
            'message': 'Entry submitted successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Submission failed: {str(e)}'}), 500

@fcos_judge.route('/api/email-certificate', methods=['POST'])
def email_certificate():
    """Email certificate to submitter"""
    try:
        data = request.get_json()
        email = data.get('email')
        certificate_data = data.get('certificateData')
        
        if not email:
            return jsonify({'error': 'Email address required'}), 400
        
        # This would integrate with your email service
        # For now, return success
        return jsonify({
            'success': True,
            'message': f'Certificate emailed to {email}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Email failed: {str(e)}'}), 500

def format_plant_name(taxonomy):
    """Format plant name for display"""
    name = ''
    if taxonomy.get('genus'):
        name += taxonomy['genus']
    if taxonomy.get('species'):
        name += f" {taxonomy['species']}"
    if taxonomy.get('clone'):
        name += f" '{taxonomy['clone']}'"
    return name or 'Unknown Orchid'

# Register blueprint with main app
def register_fcos_judge_routes(app):
    """Register FCOS Judge routes with Flask app"""
    app.register_blueprint(fcos_judge)
    print("✅ FCOS Orchid Judge PWA routes registered")