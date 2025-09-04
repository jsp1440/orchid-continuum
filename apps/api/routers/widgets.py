from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from database import get_db
from models.orchid_models import Orchid, Photo, CultureSheet
from routers.search import search_by_conditions

router = APIRouter()

# Widget embed templates
WIDGET_BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orchid Continuum Widget</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .widget-container {{ padding: 16px; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .widget-title {{ font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1a1a1a; }}
        .orchid-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }}
        .orchid-card {{ border: 1px solid #e5e5e5; border-radius: 8px; overflow: hidden; transition: transform 0.2s; }}
        .orchid-card:hover {{ transform: translateY(-2px); }}
        .orchid-image {{ width: 100%; height: 150px; object-fit: cover; }}
        .orchid-info {{ padding: 12px; }}
        .orchid-name {{ font-weight: 600; color: #2d5a87; margin-bottom: 4px; }}
        .orchid-genus {{ color: #666; font-size: 14px; }}
        .powered-by {{ text-align: center; margin-top: 16px; font-size: 12px; color: #999; }}
        .powered-by a {{ color: #2d5a87; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="widget-container">
        {content}
        <div class="powered-by">
            Powered by <a href="https://orchid-continuum.org" target="_blank">Orchid Continuum</a>
        </div>
    </div>
</body>
</html>
"""

class WidgetConfig(BaseModel):
    widget_type: str
    options: Dict[str, Any] = {}

@router.get("/finder/embed")
async def embed_finder_widget(
    light: Optional[str] = Query(None),
    temperature: Optional[str] = Query(None),
    humidity: Optional[str] = Query(None),
    limit: int = Query(6, ge=1, le=12),
    db: Session = Depends(get_db)
):
    """Embeddable widget for orchid finder by growing conditions"""
    
    # Get orchid matches
    matches = await search_by_conditions(light, temperature, humidity, limit, db)
    
    # Generate HTML content
    content = f"""
        <div class="widget-title">🌺 Orchids for Your Conditions</div>
        <div class="orchid-grid">
    """
    
    for match in matches:
        photo_url = match.primary_photo_url or "/static/placeholder-orchid.jpg"
        content += f"""
            <div class="orchid-card">
                <img src="{photo_url}" alt="{match.scientific_name}" class="orchid-image">
                <div class="orchid-info">
                    <div class="orchid-name">{match.scientific_name}</div>
                    <div class="orchid-genus">{match.genus}</div>
                </div>
            </div>
        """
    
    content += "</div>"
    
    # Wrap in template
    html = WIDGET_BASE_TEMPLATE.format(content=content)
    
    return HTMLResponse(content=html)

@router.get("/gallery/embed")
async def embed_gallery_widget(
    count: int = Query(6, ge=1, le=20),
    genus: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Embeddable rotating gallery widget"""
    
    # Build query
    query = db.query(Orchid).join(Photo).filter(Photo.is_verified == True)
    
    if genus:
        query = query.filter(Orchid.genus.ilike(f"%{genus}%"))
    
    orchids = query.limit(count).all()
    
    # Generate HTML content
    content = f"""
        <div class="widget-title">🌸 Orchid Gallery</div>
        <div class="orchid-grid">
    """
    
    for orchid in orchids:
        primary_photo = next((p for p in orchid.photos if p.is_verified), None)
        if not primary_photo:
            continue
            
        content += f"""
            <div class="orchid-card">
                <img src="{primary_photo.url}" alt="{orchid.scientific_name}" class="orchid-image">
                <div class="orchid-info">
                    <div class="orchid-name">{orchid.scientific_name}</div>
                    <div class="orchid-genus">{orchid.genus}</div>
                </div>
            </div>
        """
    
    content += "</div>"
    
    # Wrap in template
    html = WIDGET_BASE_TEMPLATE.format(content=content)
    
    return HTMLResponse(content=html)

@router.get("/care-wheel/embed/{orchid_id}")
async def embed_care_wheel_widget(
    orchid_id: str,
    db: Session = Depends(get_db)
):
    """Embeddable care wheel widget for specific orchid"""
    
    # Get orchid care data (would call the care wheel endpoint)
    # For now, return a simple template
    
    content = f"""
        <div class="widget-title">🎯 Care Wheel</div>
        <div style="text-align: center; padding: 40px;">
            <p>Care wheel for orchid {orchid_id}</p>
            <p style="color: #666; margin-top: 8px;">Interactive care visualization</p>
        </div>
    """
    
    html = WIDGET_BASE_TEMPLATE.format(content=content)
    return HTMLResponse(content=html)

@router.get("/search/embed")
async def embed_search_widget(db: Session = Depends(get_db)):
    """Embeddable search widget"""
    
    content = """
        <div class="widget-title">🔍 Search Orchids</div>
        <div style="padding: 20px;">
            <input type="text" placeholder="Search orchids..." 
                   style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px;">
            <div style="margin-top: 16px; text-align: center;">
                <button style="background: #2d5a87; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">
                    Search
                </button>
            </div>
        </div>
    """
    
    html = WIDGET_BASE_TEMPLATE.format(content=content)
    return HTMLResponse(content=html)

@router.get("/js/{widget_type}")
async def get_widget_script(widget_type: str):
    """Generate JavaScript for widget embedding"""
    
    script = f"""
(function() {{
    window.OrchidContinuum = window.OrchidContinuum || {{}};
    
    window.OrchidContinuum.mount = function(config) {{
        const {{ widget, target, options = {{}} }} = config;
        const targetEl = typeof target === 'string' ? document.querySelector(target) : target;
        
        if (!targetEl) {{
            console.error('OrchidContinuum: Target element not found');
            return;
        }}
        
        // Create iframe
        const iframe = document.createElement('iframe');
        iframe.style.width = '100%';
        iframe.style.border = 'none';
        iframe.style.borderRadius = '8px';
        
        // Build widget URL with options
        const baseUrl = window.location.origin;
        const params = new URLSearchParams(options);
        iframe.src = `${{baseUrl}}/widgets/${{widget}}/embed?${{params}}`;
        
        // Set height based on widget type
        const heights = {{
            'finder': '600px',
            'gallery': '400px',
            'care-wheel': '500px',
            'search': '200px'
        }};
        iframe.style.height = heights[widget] || '400px';
        
        targetEl.appendChild(iframe);
        
        return iframe;
    }};
    
    // Auto-initialize widgets with data attributes
    document.addEventListener('DOMContentLoaded', function() {{
        document.querySelectorAll('[data-orchid-widget]').forEach(function(el) {{
            const widget = el.getAttribute('data-orchid-widget');
            const options = {{...el.dataset}};
            delete options.orchidWidget;
            
            window.OrchidContinuum.mount({{
                widget: widget,
                target: el,
                options: options
            }});
        }});
    }});
}})();
"""
    
    return JSONResponse(
        content={"script": script},
        headers={"Content-Type": "application/json"}
    )

@router.get("/embed-help")
async def get_embed_help():
    """Documentation for embedding widgets"""
    
    help_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Orchid Continuum - Widget Embedding Guide</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
            h1, h2 { color: #2d5a87; }
            .code { background: #f5f5f5; padding: 15px; border-radius: 6px; margin: 10px 0; }
            .method { margin: 30px 0; }
        </style>
    </head>
    <body>
        <h1>🌺 Orchid Continuum Widget Embedding</h1>
        
        <h2>Method 1: Script Tag</h2>
        <div class="code">
&lt;script src="https://your-domain.com/widgets/js/all"&gt;&lt;/script&gt;
&lt;div data-orchid-widget="finder" data-light="medium" data-temperature="intermediate"&gt;&lt;/div&gt;
        </div>
        
        <h2>Method 2: Manual JavaScript</h2>
        <div class="code">
&lt;div id="orchid-finder"&gt;&lt;/div&gt;
&lt;script&gt;
OrchidContinuum.mount({
  widget: 'finder',
  target: '#orchid-finder',
  options: { light: 'medium', temperature: 'intermediate' }
});
&lt;/script&gt;
        </div>
        
        <h2>Method 3: iFrame (Safest)</h2>
        <div class="code">
&lt;iframe src="https://your-domain.com/widgets/finder/embed?light=medium&temperature=intermediate" 
        width="100%" height="600" frameborder="0"&gt;&lt;/iframe&gt;
        </div>
        
        <h2>Available Widgets</h2>
        <ul>
            <li><strong>finder</strong> - Search orchids by growing conditions</li>
            <li><strong>gallery</strong> - Rotating photo gallery</li>
            <li><strong>care-wheel</strong> - Care requirements visualization</li>
            <li><strong>search</strong> - Basic orchid search</li>
        </ul>
    </body>
    </html>
    """
    
    return HTMLResponse(content=help_html)