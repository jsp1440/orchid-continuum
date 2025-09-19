"""
Member Submission Email Template for FCOS Newsletter & Members Garden
Automated email campaigns for content collection and member engagement
"""

import os
from datetime import datetime
from typing import Dict, List

class MemberSubmissionEmailTemplate:
    """Email templates for member content submissions"""
    
    def __init__(self):
        self.current_month = datetime.now().strftime('%B %Y')
        self.submission_deadline = self._get_next_deadline()
        
        # Google Sheets link for Members Garden submissions
        self.members_garden_link = "https://docs.google.com/forms/d/e/1FAIpQLSc_MEMBERS_GARDEN_FORM_ID/viewform"
        
        # Website member area link
        self.member_gallery_link = "https://fivecitiesorchidsociety.org/members/gallery"
        
    def _get_next_deadline(self) -> str:
        """Calculate next submission deadline (typically 25th of each month)"""
        today = datetime.now()
        if today.day <= 25:
            deadline = today.replace(day=25)
        else:
            # Next month's 25th
            if today.month == 12:
                deadline = today.replace(year=today.year + 1, month=1, day=25)
            else:
                deadline = today.replace(month=today.month + 1, day=25)
        
        return deadline.strftime('%B %d, %Y')
    
    def generate_main_submission_email(self) -> Dict[str, str]:
        """Generate the main member submission request email"""
        
        email_content = {
            'subject': f'🌺 Share Your Orchid Story - {self.current_month} Newsletter Submissions',
            'preheader': 'Help create our community newsletter with your orchid photos and stories!',
            'html_content': f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FCOS Newsletter Submissions</title>
    <style>
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .header {{
            background: linear-gradient(135deg, #2E8B57, #228B22);
            color: white;
            padding: 30px 20px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            padding: 30px 20px;
            background: white;
            border: 2px solid #2E8B57;
            border-top: none;
        }}
        .submission-box {{
            background: #f8f9fa;
            border-left: 5px solid #2E8B57;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, #2E8B57, #228B22);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }}
        .feature-card {{
            background: #E8F5E8;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
            color: #666;
            border-radius: 0 0 10px 10px;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🌺 Share Your Orchid Journey!</h1>
            <p>Help us create our {self.current_month} newsletter together</p>
        </div>
        
        <div class="content">
            <p>Dear FCOS Member,</p>
            
            <p>Our community newsletter is only as vibrant as the stories and photos you share! We're looking for your contributions to make our {self.current_month} edition truly special.</p>
            
            <div class="submission-box">
                <h3>🎯 What We're Looking For:</h3>
                <ul>
                    <li><strong>📸 Orchid Photos</strong> - Your best blooms, unique specimens, or growing setups</li>
                    <li><strong>📝 Growing Stories</strong> - Success stories, challenges overcome, or tips learned</li>
                    <li><strong>📰 Articles</strong> - Care guides, species spotlights, or technique tutorials</li>
                    <li><strong>🎥 Videos</strong> - Repotting demos, bloom time-lapses, or care walkthroughs</li>
                    <li><strong>🌟 Member Features</strong> - Get highlighted on our YouTube channel!</li>
                </ul>
            </div>
            
            <h3>📋 Photo Submission Requirements:</h3>
            <p>When submitting orchid photos, please include:</p>
            <ul>
                <li><strong>Genus & Species</strong> (or hybrid name if known)</li>
                <li><strong>How you grow it</strong> - Growing medium, light, water schedule, etc.</li>
                <li><strong>Your name</strong> - How you'd like to be credited</li>
                <li><strong>Email address</strong> - For follow-up questions</li>
                <li><strong>City/Location</strong> - Helps others in similar climates</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{self.members_garden_link}" class="cta-button">
                    🌱 Submit to Members Garden
                </a>
            </div>
            
            <div class="features-grid">
                <div class="feature-card">
                    <h4>📧 Newsletter Feature</h4>
                    <p>Your photos and stories could be featured in our monthly newsletter reaching all FCOS members</p>
                </div>
                <div class="feature-card">
                    <h4>🌐 Website Gallery</h4>
                    <p>Photos appear on our new website in the members area - your personal orchid showcase</p>
                </div>
                <div class="feature-card">
                    <h4>📱 Personal Gallery</h4>
                    <p>Access your own gallery in the members area at <a href="{self.member_gallery_link}">fivecitiesorchidsociety.org</a></p>
                </div>
            </div>
            
            <div class="submission-box">
                <h3>🎬 YouTube Channel Features</h3>
                <p>Want to be featured on our YouTube channel? We're looking for:</p>
                <ul>
                    <li>Collection tours and growing space showcases</li>
                    <li>Repotting or care technique demonstrations</li>
                    <li>Orchid rescue and recovery stories</li>
                    <li>Seasonal care routine walkthroughs</li>
                </ul>
                <p><em>Contact us if interested - we can help with filming and editing!</em></p>
            </div>
            
            <h3>📅 Important Dates:</h3>
            <p><strong>Submission Deadline:</strong> {self.submission_deadline}</p>
            <p><strong>Newsletter Publication:</strong> First week of next month</p>
            
            <p>Your contributions make our community stronger and help fellow orchid enthusiasts learn and grow. Every photo, tip, and story shared helps build our collective knowledge.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{self.members_garden_link}" class="cta-button">
                    📤 Submit Your Content Now
                </a>
            </div>
            
            <p>Questions about submissions? Reply to this email or contact us at <a href="mailto:newsletter@fivecitiesorchidsociety.org">newsletter@fivecitiesorchidsociety.org</a></p>
            
            <p>Thank you for being such an important part of our orchid community!</p>
            
            <p>Growing together,<br>
            <strong>Five Cities Orchid Society Newsletter Team</strong></p>
        </div>
        
        <div class="footer">
            <p>Five Cities Orchid Society | Connecting Orchid Enthusiasts Since 1990</p>
            <p>Visit our website: <a href="https://fivecitiesorchidsociety.org">fivecitiesorchidsociety.org</a></p>
            <p>Follow us for daily orchid inspiration and community updates</p>
        </div>
    </div>
</body>
</html>
            """,
            'plain_text': f"""
🌺 SHARE YOUR ORCHID JOURNEY - {self.current_month.upper()} NEWSLETTER SUBMISSIONS

Dear FCOS Member,

Our community newsletter is only as vibrant as the stories and photos you share! We're looking for your contributions to make our {self.current_month} edition truly special.

WHAT WE'RE LOOKING FOR:
• 📸 Orchid Photos - Your best blooms, unique specimens, or growing setups
• 📝 Growing Stories - Success stories, challenges overcome, or tips learned  
• 📰 Articles - Care guides, species spotlights, or technique tutorials
• 🎥 Videos - Repotting demos, bloom time-lapses, or care walkthroughs
• 🌟 Member Features - Get highlighted on our YouTube channel!

PHOTO SUBMISSION REQUIREMENTS:
When submitting orchid photos, please include:
• Genus & Species (or hybrid name if known)
• How you grow it - Growing medium, light, water schedule, etc.
• Your name - How you'd like to be credited
• Email address - For follow-up questions  
• City/Location - Helps others in similar climates

SUBMIT YOUR CONTENT: {self.members_garden_link}

YOUR PHOTOS WILL APPEAR IN:
✓ Monthly newsletter reaching all FCOS members
✓ Website gallery in the members area
✓ Your personal gallery at {self.member_gallery_link}

YOUTUBE CHANNEL FEATURES:
Want to be featured? We're looking for:
• Collection tours and growing space showcases
• Repotting or care technique demonstrations
• Orchid rescue and recovery stories
• Seasonal care routine walkthroughs

IMPORTANT DATES:
Submission Deadline: {self.submission_deadline}
Newsletter Publication: First week of next month

Your contributions make our community stronger and help fellow orchid enthusiasts learn and grow.

SUBMIT NOW: {self.members_garden_link}

Questions? Contact: newsletter@fivecitiesorchidsociety.org

Thank you for being such an important part of our orchid community!

Growing together,
Five Cities Orchid Society Newsletter Team

---
Five Cities Orchid Society | fivecitiesorchidsociety.org
Connecting Orchid Enthusiasts Since 1990
            """
        }
        
        return email_content
    
    def generate_reminder_email(self) -> Dict[str, str]:
        """Generate a gentle reminder email for submission deadline"""
        
        email_content = {
            'subject': f'⏰ Last Call - Newsletter Submissions Due {self.submission_deadline}',
            'preheader': 'Don\'t miss your chance to be featured in this month\'s newsletter!',
            'html_content': f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .urgent-header {{
            background: linear-gradient(135deg, #FF6B35, #F7931E);
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            padding: 20px;
            background: white;
            border: 2px solid #FF6B35;
            border-top: none;
            border-radius: 0 0 10px 10px;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, #FF6B35, #F7931E);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="urgent-header">
            <h1>⏰ Last Call for Submissions!</h1>
            <p>Deadline: {self.submission_deadline}</p>
        </div>
        
        <div class="content">
            <p>Hi there!</p>
            
            <p>Just a friendly reminder that we're still accepting submissions for our {self.current_month} newsletter!</p>
            
            <p><strong>We'd love to feature:</strong></p>
            <ul>
                <li>Your recent orchid blooms 🌸</li>
                <li>Growing tips that work for you 🌱</li>
                <li>Success stories or rescue tales 📖</li>
                <li>Questions for our community Q&A 🤔</li>
            </ul>
            
            <div style="text-align: center; margin: 25px 0;">
                <a href="{self.members_garden_link}" class="cta-button">
                    Submit Before {self.submission_deadline}
                </a>
            </div>
            
            <p>Even a single photo with a quick note about how you grow it helps other members learn!</p>
            
            <p>Thanks for considering sharing with our community.</p>
            
            <p>Best,<br>FCOS Newsletter Team</p>
        </div>
    </div>
</body>
</html>
            """,
            'plain_text': f"""
⏰ LAST CALL FOR NEWSLETTER SUBMISSIONS

Hi there!

Just a friendly reminder that we're still accepting submissions for our {self.current_month} newsletter!

DEADLINE: {self.submission_deadline}

WE'D LOVE TO FEATURE:
• Your recent orchid blooms 🌸
• Growing tips that work for you 🌱  
• Success stories or rescue tales 📖
• Questions for our community Q&A 🤔

SUBMIT NOW: {self.members_garden_link}

Even a single photo with a quick note about how you grow it helps other members learn!

Thanks for considering sharing with our community.

Best,
FCOS Newsletter Team
            """
        }
        
        return email_content
    
    def generate_thank_you_email(self) -> Dict[str, str]:
        """Generate thank you email for members who submitted content"""
        
        email_content = {
            'subject': '🙏 Thank You for Your Newsletter Submission!',
            'preheader': 'Your contribution helps make our community stronger',
            'html_content': f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .thank-you-header {{
            background: linear-gradient(135deg, #2E8B57, #228B22);
            color: white;
            padding: 25px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            padding: 25px;
            background: white;
            border: 2px solid #2E8B57;
            border-top: none;
            border-radius: 0 0 10px 10px;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="thank-you-header">
            <h1>🙏 Thank You!</h1>
            <p>Your submission has been received</p>
        </div>
        
        <div class="content">
            <p>Dear FCOS Member,</p>
            
            <p>Thank you so much for contributing to our {self.current_month} newsletter! Your photos, stories, and insights are what make our community publication truly special.</p>
            
            <p><strong>What happens next:</strong></p>
            <ul>
                <li>📝 Our team will review your submission</li>
                <li>📧 We may contact you for additional details</li>
                <li>🌐 Your photos will be added to your member gallery</li>
                <li>📰 Featured content will appear in the newsletter</li>
                <li>📬 Newsletter publication: First week of next month</li>
            </ul>
            
            <p>Your contribution helps fellow orchid enthusiasts learn and grow. Every photo, tip, and story shared builds our collective knowledge and strengthens our community bonds.</p>
            
            <p>Keep an eye out for the newsletter - we can't wait for you to see how your contribution fits into this month's edition!</p>
            
            <p>With gratitude,<br>
            <strong>Five Cities Orchid Society Newsletter Team</strong></p>
            
            <p><em>P.S. Check your member gallery at <a href="{self.member_gallery_link}">fivecitiesorchidsociety.org</a> to see your photos once they're processed!</em></p>
        </div>
    </div>
</body>
</html>
            """,
            'plain_text': f"""
🙏 THANK YOU FOR YOUR NEWSLETTER SUBMISSION!

Dear FCOS Member,

Thank you so much for contributing to our {self.current_month} newsletter! Your photos, stories, and insights are what make our community publication truly special.

WHAT HAPPENS NEXT:
• 📝 Our team will review your submission
• 📧 We may contact you for additional details  
• 🌐 Your photos will be added to your member gallery
• 📰 Featured content will appear in the newsletter
• 📬 Newsletter publication: First week of next month

Your contribution helps fellow orchid enthusiasts learn and grow. Every photo, tip, and story shared builds our collective knowledge.

Keep an eye out for the newsletter - we can't wait for you to see how your contribution fits into this month's edition!

With gratitude,
Five Cities Orchid Society Newsletter Team

P.S. Check your member gallery at {self.member_gallery_link} to see your photos once they're processed!
            """
        }
        
        return email_content

# Initialize the email template generator
submission_email_generator = MemberSubmissionEmailTemplate()

# Export for use in Neon One integration
__all__ = ['MemberSubmissionEmailTemplate', 'submission_email_generator']