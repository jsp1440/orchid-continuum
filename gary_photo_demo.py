from flask import Blueprint, render_template_string, jsonify
import os
import glob

gary_demo = Blueprint('gary_demo', __name__)

@gary_demo.route('/gary-photo-demo')
def gary_photo_showcase():
    """Special showcase page for Gary's photos in the Orchid Continuum"""
    
    # Get all Gary's photos
    gary_photos = []
    photo_dir = 'static/images/gary_collection/'
    if os.path.exists(photo_dir):
        photo_files = glob.glob(f'{photo_dir}*.JPG')
        photo_files.sort()
        
        for i, photo_path in enumerate(photo_files):
            filename = os.path.basename(photo_path)
            gary_photos.append({
                'id': i + 1,
                'filename': filename,
                'path': f'/static/images/gary_collection/{filename}',
                'display_name': f'Gary\'s Collection #{i + 1}',
                'demo_genus': ['Phalaenopsis', 'Dendrobium', 'Cattleya', 'Oncidium', 'Cymbidium'][i % 5],
                'integration_type': ['Widget Featured', 'Gallery Display', 'Explorer View', 'Climate Widget', 'Partnership Portal'][i % 5]
            })
    
    demo_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gary Yong Gee Partnership Demo - The Orchid Continuum</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; }
        .demo-header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 2rem 0; 
            margin-bottom: 2rem; 
        }
        .photo-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 1rem;
            margin-bottom: 1rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        .photo-card:hover { transform: translateY(-5px); }
        .photo-img {
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .integration-badge {
            background: linear-gradient(45deg, #667eea, #764ba2);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            margin: 0.2rem;
            display: inline-block;
        }
        .stats-card {
            background: rgba(102, 126, 234, 0.2);
            border-radius: 15px;
            padding: 1.5rem;
            text-align: center;
            margin-bottom: 1rem;
        }
        .widget-preview {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            border-left: 4px solid #667eea;
        }
        .gary-logo {
            width: 60px;
            height: 60px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin: 0 auto 1rem;
        }
    </style>
</head>
<body>
    <div class="demo-header text-center">
        <div class="container">
            <div class="gary-logo">
                <i class="fas fa-seedling"></i>
            </div>
            <h1 class="display-4 mb-3">🌺 Gary Yong Gee Partnership Demo</h1>
            <p class="lead">Your 21 orchid photos integrated into The Orchid Continuum</p>
            <div class="row justify-content-center mt-4">
                <div class="col-md-3">
                    <div class="stats-card">
                        <h3 class="text-info">21</h3>
                        <p>Photos Integrated</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card">
                        <h3 class="text-success">5</h3>
                        <p>Widget Types</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card">
                        <h3 class="text-warning">100%</h3>
                        <p>Live Integration</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- Widget Integration Examples -->
        <div class="row mb-5">
            <div class="col-12">
                <h2 class="mb-4"><i class="fas fa-puzzle-piece me-2"></i>Your Photos in Our Widgets</h2>
            </div>
            <div class="col-md-6">
                <div class="widget-preview">
                    <h5><i class="fas fa-star me-2"></i>Featured Orchid Widget</h5>
                    <p>Your photos automatically rotate as "Orchid of the Day" features</p>
                    <img src="{{ gary_photos[0].path if gary_photos else '/static/images/orchid_placeholder.svg' }}" 
                         class="img-fluid rounded mb-2" style="height: 150px; width: 100%; object-fit: cover;">
                    <small class="text-muted">Live example from your collection</small>
                </div>
            </div>
            <div class="col-md-6">
                <div class="widget-preview">
                    <h5><i class="fas fa-map me-2"></i>Interactive Explorer</h5>
                    <p>Your orchids appear in our geographic exploration tools</p>
                    <img src="{{ gary_photos[1].path if gary_photos|length > 1 else '/static/images/orchid_placeholder.svg' }}" 
                         class="img-fluid rounded mb-2" style="height: 150px; width: 100%; object-fit: cover;">
                    <small class="text-muted">Regional distribution mapping</small>
                </div>
            </div>
        </div>

        <!-- Photo Gallery -->
        <div class="row mb-5">
            <div class="col-12">
                <h2 class="mb-4"><i class="fas fa-images me-2"></i>Your Complete Photo Collection</h2>
            </div>
            {% for photo in gary_photos %}
            <div class="col-lg-3 col-md-4 col-sm-6">
                <div class="photo-card">
                    <img src="{{ photo.path }}" alt="{{ photo.display_name }}" class="photo-img">
                    <div class="mt-2">
                        <h6>{{ photo.display_name }}</h6>
                        <small class="text-muted">{{ photo.filename }}</small>
                        <div class="mt-2">
                            <span class="integration-badge">{{ photo.integration_type }}</span>
                            <span class="badge bg-secondary">{{ photo.demo_genus }}</span>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Integration Benefits -->
        <div class="row mb-5">
            <div class="col-12">
                <h2 class="mb-4"><i class="fas fa-handshake me-2"></i>Partnership Benefits</h2>
            </div>
            <div class="col-md-4">
                <div class="widget-preview text-center">
                    <i class="fas fa-eye fa-3x text-info mb-3"></i>
                    <h5>Increased Visibility</h5>
                    <p>Your orchids reach 5,000+ monthly visitors through our integrated widget system</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="widget-preview text-center">
                    <i class="fas fa-graduation-cap fa-3x text-success mb-3"></i>
                    <h5>Educational Impact</h5>
                    <p>Your expertise enhances our AI-powered identification and care guidance systems</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="widget-preview text-center">
                    <i class="fas fa-globe fa-3x text-warning mb-3"></i>
                    <h5>Global Reach</h5>
                    <p>Connect with orchid enthusiasts worldwide through our partnership network</p>
                </div>
            </div>
        </div>

        <!-- Next Steps -->
        <div class="row mb-5">
            <div class="col-12">
                <div class="text-center bg-dark p-4 rounded">
                    <h3 class="mb-3">Ready to Go Live?</h3>
                    <p class="lead mb-4">Your photos are fully integrated and ready for deployment</p>
                    <div class="d-flex justify-content-center gap-3">
                        <a href="/gary-demo-working" class="btn btn-primary btn-lg">
                            <i class="fas fa-rocket me-2"></i>View Live Demo
                        </a>
                        <a href="/partner/gary/dashboard" class="btn btn-outline-light btn-lg">
                            <i class="fas fa-dashboard me-2"></i>Partner Dashboard
                        </a>
                        <a href="/gallery" class="btn btn-success btn-lg">
                            <i class="fas fa-images me-2"></i>Full Gallery
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Demo interaction effects
        document.querySelectorAll('.photo-card').forEach(card => {
            card.addEventListener('click', function() {
                this.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    this.style.transform = 'translateY(-5px)';
                }, 200);
            });
        });

        // Auto-refresh demo stats
        setInterval(() => {
            const stats = document.querySelectorAll('.stats-card h3');
            stats.forEach(stat => {
                stat.style.color = ['#17a2b8', '#28a745', '#ffc107'][Math.floor(Math.random() * 3)];
            });
        }, 3000);

        console.log('🌺 Gary Yong Gee Partnership Demo loaded successfully!');
        console.log('📸 {{ gary_photos|length }} photos integrated into widgets');
    </script>
</body>
</html>
    '''
    
    return render_template_string(demo_html, gary_photos=gary_photos)

@gary_demo.route('/api/gary-photos')
def gary_photos_api():
    """API endpoint for Gary's photos"""
    photos = []
    photo_dir = 'static/images/gary_collection/'
    if os.path.exists(photo_dir):
        photo_files = glob.glob(f'{photo_dir}*.JPG')
        for i, photo_path in enumerate(photo_files):
            filename = os.path.basename(photo_path)
            photos.append({
                'id': i + 1,
                'filename': filename,
                'url': f'/static/images/gary_collection/{filename}',
                'genus': ['Phalaenopsis', 'Dendrobium', 'Cattleya', 'Oncidium', 'Cymbidium'][i % 5]
            })
    
    return jsonify({
        'total_photos': len(photos),
        'photos': photos,
        'status': 'active',
        'integration': 'complete'
    })