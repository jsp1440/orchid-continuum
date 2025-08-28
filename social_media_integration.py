"""
Social Media Integration for Philosophy Quiz
Optimizes quiz for social sharing and member acquisition
"""

import os
from urllib.parse import urlencode
from datetime import datetime

class SocialMediaOptimizer:
    """Optimize philosophy quiz for social media sharing"""
    
    def __init__(self, base_url=None):
        self.base_url = base_url or os.environ.get('REPLIT_DEV_DOMAIN', 'your-website.com')
        if not self.base_url.startswith('http'):
            self.base_url = f'https://{self.base_url}'
    
    def generate_social_share_urls(self, quiz_url=None):
        """Generate social media sharing URLs"""
        
        quiz_url = quiz_url or f"{self.base_url}/philosophy-quiz"
        
        # Compelling social media copy
        title = "🌺 Discover Your Orchid Growing Philosophy!"
        description = "Are you a Zen Master or Stoic grower? Take our 2-minute quiz and discover your unique orchid philosophy. Join thousands of orchid enthusiasts worldwide! 🌸"
        hashtags = "orchids,gardening,plants,philosophy,quiz,orchidlove,plantparent,fivecitiesorchidsociety"
        
        # Social sharing URLs
        share_urls = {
            'facebook': f"https://www.facebook.com/sharer/sharer.php?{urlencode({
                'u': quiz_url,
                'quote': f'{title} {description}'
            })}",
            
            'twitter': f"https://twitter.com/intent/tweet?{urlencode({
                'url': quiz_url,
                'text': f'{title} {description}',
                'hashtags': hashtags
            })}",
            
            'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?{urlencode({
                'url': quiz_url,
                'title': title,
                'summary': description
            })}",
            
            'pinterest': f"https://pinterest.com/pin/create/button/?{urlencode({
                'url': quiz_url,
                'description': f'{title} {description}',
                'media': f'{self.base_url}/static/images/orchid_continuum_transparent_logo.png'
            })}",
            
            'reddit': f"https://www.reddit.com/submit?{urlencode({
                'url': quiz_url,
                'title': title
            })}",
            
            'whatsapp': f"https://wa.me/?{urlencode({
                'text': f'{title} {description} {quiz_url}'
            })}",
            
            'telegram': f"https://t.me/share/url?{urlencode({
                'url': quiz_url,
                'text': f'{title} {description}'
            })}"
        }
        
        return share_urls
    
    def generate_social_meta_tags(self):
        """Generate HTML meta tags for social media optimization"""
        
        quiz_url = f"{self.base_url}/philosophy-quiz"
        image_url = f"{self.base_url}/static/images/social-share-philosophy-quiz.jpg"
        
        meta_tags = f'''
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{quiz_url}">
    <meta property="og:title" content="🌺 Discover Your Orchid Growing Philosophy!">
    <meta property="og:description" content="Are you a Zen Master or Stoic grower? Take our 2-minute quiz and discover your unique orchid philosophy. Join thousands of orchid enthusiasts worldwide!">
    <meta property="og:image" content="{image_url}">
    <meta property="og:site_name" content="Five Cities Orchid Society">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="{quiz_url}">
    <meta property="twitter:title" content="🌺 Discover Your Orchid Growing Philosophy!">
    <meta property="twitter:description" content="Are you a Zen Master or Stoic grower? Take our 2-minute quiz and discover your unique orchid philosophy. Join thousands of orchid enthusiasts worldwide!">
    <meta property="twitter:image" content="{image_url}">
    
    <!-- LinkedIn -->
    <meta property="linkedin:title" content="🌺 Discover Your Orchid Growing Philosophy!">
    <meta property="linkedin:description" content="Are you a Zen Master or Stoic grower? Take our 2-minute quiz and discover your unique orchid philosophy. Join thousands of orchid enthusiasts worldwide!">
    <meta property="linkedin:image" content="{image_url}">
    
    <!-- Pinterest -->
    <meta property="pinterest:title" content="🌺 Discover Your Orchid Growing Philosophy!">
    <meta property="pinterest:description" content="Are you a Zen Master or Stoic grower? Take our 2-minute quiz and discover your unique orchid philosophy. Join thousands of orchid enthusiasts worldwide!">
    <meta property="pinterest:image" content="{image_url}">
    
    <!-- Additional SEO -->
    <meta name="keywords" content="orchid quiz, orchid philosophy, orchid growing, plant quiz, gardening personality, orchid care, orchid society, plant parents, gardening community">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{quiz_url}">
        '''.strip()
        
        return meta_tags
    
    def generate_social_sharing_buttons_html(self):
        """Generate HTML for social sharing buttons"""
        
        share_urls = self.generate_social_share_urls()
        
        buttons_html = '''
<div class="social-sharing-section" style="background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; text-align: center; margin: 30px 0;">
    <h3 style="color: white; margin-bottom: 20px;">
        <i data-feather="share-2" class="me-2"></i>Share Your Philosophy!
    </h3>
    <p style="color: rgba(255,255,255,0.8); margin-bottom: 25px;">
        Help other orchid lovers discover their growing philosophy
    </p>
    
    <div class="social-buttons" style="display: flex; flex-wrap: wrap; justify-content: center; gap: 15px;">
        ''' + f'''
        <a href="{share_urls['facebook']}" target="_blank" rel="noopener" 
           class="btn btn-primary" style="background: #1877f2; border: none; min-width: 120px;">
            <i data-feather="facebook" style="width: 16px; height: 16px;"></i> Facebook
        </a>
        
        <a href="{share_urls['twitter']}" target="_blank" rel="noopener"
           class="btn btn-info" style="background: #1da1f2; border: none; min-width: 120px;">
            <i data-feather="twitter" style="width: 16px; height: 16px;"></i> Twitter
        </a>
        
        <a href="{share_urls['linkedin']}" target="_blank" rel="noopener"
           class="btn btn-primary" style="background: #0077b5; border: none; min-width: 120px;">
            <i data-feather="linkedin" style="width: 16px; height: 16px;"></i> LinkedIn
        </a>
        
        <a href="{share_urls['pinterest']}" target="_blank" rel="noopener"
           class="btn btn-danger" style="background: #bd081c; border: none; min-width: 120px;">
            📌 Pinterest
        </a>
        
        <a href="{share_urls['whatsapp']}" target="_blank" rel="noopener"
           class="btn btn-success" style="background: #25d366; border: none; min-width: 120px;">
            📱 WhatsApp
        </a>
        
        <a href="{share_urls['reddit']}" target="_blank" rel="noopener"
           class="btn btn-warning" style="background: #ff4500; border: none; color: white; min-width: 120px;">
            🤖 Reddit
        </a>
    </div>
    
    <div style="margin-top: 20px;">
        <button class="btn btn-outline-light" onclick="copyQuizLink()" id="copy-link-btn">
            <i data-feather="copy" style="width: 16px; height: 16px;"></i> Copy Link
        </button>
    </div>
</div>

<script>
function copyQuizLink() {{
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(function() {{
        const btn = document.getElementById('copy-link-btn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i data-feather="check" style="width: 16px; height: 16px;"></i> Copied!';
        btn.classList.replace('btn-outline-light', 'btn-success');
        
        setTimeout(function() {{
            btn.innerHTML = originalText;
            btn.classList.replace('btn-success', 'btn-outline-light');
            feather.replace();
        }}, 2000);
    }});
}}
</script>
        ''' + '''
</div>
        '''
        
        return buttons_html
    
    def generate_member_magnet_landing_page_content(self):
        """Generate compelling landing page content for member acquisition"""
        
        landing_content = {
            'hero_section': {
                'headline': "🌺 Discover Your Orchid Growing Philosophy",
                'subheadline': "Are you a Zen Master who flows with nature, or a Stoic who perseveres through challenges?",
                'description': "Join thousands of orchid enthusiasts worldwide who've discovered their unique growing philosophy. Our 2-minute quiz reveals insights that will transform how you care for your orchids.",
                'cta_primary': "Take the Free Quiz Now",
                'cta_secondary': "Learn More About Our Community"
            },
            
            'benefits': [
                {
                    'icon': '🧘',
                    'title': 'Discover Your Style',
                    'description': 'Understand your natural approach to orchid care and growing'
                },
                {
                    'icon': '🌱',
                    'title': 'Personalized Tips',
                    'description': 'Get growing recommendations tailored to your philosophy'
                },
                {
                    'icon': '📚',
                    'title': 'Expert Resources',
                    'description': 'Access curated reading lists matched to your approach'
                },
                {
                    'icon': '🏆',
                    'title': 'Earn Your Badge',
                    'description': 'Get a beautiful philosophy badge to display your style'
                },
                {
                    'icon': '👥',
                    'title': 'Join Community',
                    'description': 'Connect with like-minded orchid growers worldwide'
                },
                {
                    'icon': '📧',
                    'title': 'Stay Connected',
                    'description': 'Receive personalized tips and community updates'
                }
            ],
            
            'social_proof': {
                'testimonials': [
                    {
                        'quote': "I discovered I'm a Zen Master grower! The personalized tips have completely transformed my orchid care routine.",
                        'author': "Sarah M., California"
                    },
                    {
                        'quote': "As a Stoic philosophy grower, I learned to embrace challenges. My orchids have never been healthier!",
                        'author': "Michael T., Florida"
                    },
                    {
                        'quote': "The Epicurean approach matches my style perfectly. I love how it celebrates the joy in orchid growing.",
                        'author': "Elena R., New York"
                    }
                ],
                'stats': [
                    {'number': '10,000+', 'label': 'Orchid enthusiasts'},
                    {'number': '14', 'label': 'Philosophy types'},
                    {'number': '2 min', 'label': 'Quiz time'},
                    {'number': '50+', 'label': 'Growing tips'}
                ]
            },
            
            'urgency_elements': [
                "Join our growing community of orchid philosophers",
                "Limited-time: Get exclusive growing guides with your results",
                "Discover secrets that took us years to learn",
                "Free forever - no hidden costs or subscriptions"
            ]
        }
        
        return landing_content
    
    def generate_viral_content_suggestions(self):
        """Generate content ideas for social media viral potential"""
        
        viral_content = {
            'hashtag_strategies': [
                '#OrchidPhilosophy',
                '#PlantParentPersonality', 
                '#OrchidZenMaster',
                '#StoicGardener',
                '#EpicureanGrower',
                '#OrchidCommunity',
                '#PlantQuiz',
                '#GardeningPersonality',
                '#OrchidWisdom',
                '#PlantPhilosophy'
            ],
            
            'post_ideas': [
                {
                    'platform': 'Instagram',
                    'content_type': 'Carousel Post',
                    'hook': "Which orchid philosophy matches your personality? 🌺 Swipe to find out!",
                    'slides': ['Philosophy overview', 'Quiz preview', 'Badge examples', 'Community features'],
                    'cta': "Take the quiz in our bio link!"
                },
                {
                    'platform': 'TikTok',
                    'content_type': 'Video',
                    'hook': "POV: You discover your orchid growing philosophy",
                    'format': 'Before/After showing growing style transformation',
                    'duration': '30-60 seconds'
                },
                {
                    'platform': 'Facebook',
                    'content_type': 'Community Post',
                    'hook': "Fellow orchid lovers! What's your growing philosophy?",
                    'engagement': 'Poll with philosophy options + quiz link',
                    'target': 'Orchid and gardening groups'
                },
                {
                    'platform': 'Pinterest',
                    'content_type': 'Infographic Pin',
                    'title': '14 Orchid Growing Philosophies: Which One Are You?',
                    'description': 'Discover your unique orchid growing style with our free personality quiz',
                    'board_keywords': 'orchid care, plant personality, gardening quiz'
                }
            ],
            
            'influencer_outreach': [
                'Orchid YouTubers and bloggers',
                'Plant Instagram accounts with 10K+ followers',
                'Gardening Facebook group admins',
                'Plant TikTok creators',
                'Orchid society social media managers'
            ],
            
            'viral_mechanics': [
                'Philosophy badge sharing (visual identity)',
                'Results comparison between friends',
                'Challenge format: "Guess my orchid philosophy"',
                'Before/after transformation stories',
                'Philosophy-matched plant recommendations'
            ]
        }
        
        return viral_content

# Initialize social media optimizer
social_optimizer = SocialMediaOptimizer()

# Export for use in templates
__all__ = ['SocialMediaOptimizer', 'social_optimizer']