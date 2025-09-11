from flask import Response
from authentic_philosophy_data import PHILOSOPHY_DATA

def create_badge_test_page():
    """Create a test page to display all philosophy badges"""
    
    html_template = '''<!DOCTYPE html>
<html>
<head>
    <title>Badge Display Test</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background: #333; color: white; }}
        .badge-test {{ 
            margin: 20px 0; 
            padding: 20px; 
            border: 1px solid #666; 
            border-radius: 10px;
            background: #444;
        }}
        .badge-img {{ 
            width: 100px; 
            height: 100px; 
            border: 2px solid #fff; 
            border-radius: 50%; 
            object-fit: cover;
            margin-right: 20px;
        }}
        .badge-row {{
            display: flex;
            align-items: center;
        }}
        .error {{ color: #ff6b6b; }}
        .success {{ color: #51cf66; }}
    </style>
</head>
<body>
    <h1>All Philosophy Badges Test</h1>
    {badge_sections}
    <script>
        const images = document.querySelectorAll('.badge-img');
        images.forEach(img => {{
            img.addEventListener('load', function() {{
                const status = this.parentElement.querySelector('.success');
                if (status) {{
                    status.innerHTML = '✅ LOADED';
                    status.className = 'success';
                }}
            }});
            
            img.addEventListener('error', function() {{
                const status = this.parentElement.querySelector('.success');
                if (status) {{
                    status.innerHTML = '❌ FAILED';
                    status.className = 'error';
                }}
                this.style.border = '2px solid red';
            }});
        }});
    </script>
</body>
</html>'''

    badge_sections = ""
    for name, data in PHILOSOPHY_DATA.items():
        badge_sections += f'''
    <div class="badge-test">
        <div class="badge-row">
            <img src="{data['badge_link']}" class="badge-img">
            <div>
                <h3>{name} <span class="success">✓</span></h3>
                <p>URL: {data['badge_link']}</p>
            </div>
        </div>
    </div>'''
    
    return html_template.format(badge_sections=badge_sections)