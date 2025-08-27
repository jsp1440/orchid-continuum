#!/usr/bin/env python3
"""
Test static photo serving for orchids
"""

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Static Photo Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container my-5">
        <h1>Five Cities Orchid Society - Static Photos Test</h1>
        <div class="row" id="orchid-gallery">
            <!-- Photos loaded by JavaScript -->
        </div>
    </div>
    
    <script>
        fetch('/api/static-orchids')
            .then(response => response.json())
            .then(orchids => {
                let html = '';
                orchids.forEach(orchid => {
                    html += `
                        <div class="col-md-3 mb-4">
                            <div class="card">
                                <img src="${orchid.image_url}" 
                                     class="card-img-top" 
                                     style="height: 200px; object-fit: cover;" 
                                     alt="${orchid.display_name}">
                                <div class="card-body">
                                    <h6 class="card-title">${orchid.display_name}</h6>
                                    <p class="card-text small">${orchid.ai_description}</p>
                                </div>
                            </div>
                        </div>
                    `;
                });
                document.getElementById('orchid-gallery').innerHTML = html;
            });
    </script>
</body>
</html>
    ''')

@app.route('/api/static-orchids')
def static_orchids():
    """Test static orchid photos"""
    return jsonify([
        {
            "id": 1,
            "scientific_name": "Cattleya trianae",
            "display_name": "Cattleya trianae",
            "photographer": "Five Cities Orchid Society",
            "ai_description": "Beautiful purple Christmas orchid in full bloom",
            "image_url": "/static/orchid_photos/cattleya.png"
        },
        {
            "id": 2,
            "scientific_name": "Phalaenopsis amabilis",
            "display_name": "Phalaenopsis amabilis", 
            "photographer": "Five Cities Orchid Society",
            "ai_description": "Elegant white moon orchid",
            "image_url": "/static/orchid_photos/phalaenopsis.png"
        },
        {
            "id": 3,
            "scientific_name": "Dendrobium nobile",
            "display_name": "Dendrobium nobile",
            "photographer": "Five Cities Orchid Society", 
            "ai_description": "Pink and purple noble dendrobium",
            "image_url": "/static/orchid_photos/dendrobium.png"
        },
        {
            "id": 4,
            "scientific_name": "Vanda coerulea",
            "display_name": "Vanda coerulea",
            "photographer": "Five Cities Orchid Society",
            "ai_description": "Stunning blue vanda orchid",
            "image_url": "/static/orchid_photos/vanda.png"
        }
    ])

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5007, debug=True)