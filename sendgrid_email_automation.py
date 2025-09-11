"""
Complete SendGrid Email Automation System for Philosophy Quiz
Based on the authentic data from the response file
"""

import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, From, Content
from authentic_philosophy_data import get_philosophy_data, PHILOSOPHY_DATA

class PhilosophyQuizEmailer:
    def __init__(self):
        self.sg = SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        self.from_email = From("noreply@fcos.org", "Five Cities Orchid Society")
        self.logo_url = "https://i.imgur.com/WK10q2B.png"
        
    def send_philosophy_result_email(self, user_email, user_name, philosophy_result):
        """Send personalized philosophy result email with badge and insights"""
        try:
            # Get the complete authentic data for this philosophy
            phil_data = get_philosophy_data(philosophy_result)
            if not phil_data:
                logging.error(f"No data found for philosophy: {philosophy_result}")
                return False
                
            # Build the complete HTML email using authentic data
            html_content = self.build_complete_email_html(
                user_name=user_name,
                philosophy_title=philosophy_result,
                phil_data=phil_data
            )
            
            # Create and send email
            mail = Mail(
                from_email=self.from_email,
                to_emails=To(user_email),
                subject=f"Your Orchid Philosophy: {philosophy_result}",
                html_content=Content("text/html", html_content)
            )
            
            response = self.sg.send(mail)
            logging.info(f"Email sent successfully to {user_email}. Status: {response.status_code}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email to {user_email}: {str(e)}")
            return False
    
    def build_complete_email_html(self, user_name, philosophy_title, phil_data):
        """Build the complete professional email HTML using authentic data"""
        safe_name = user_name or 'Friend'
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Orchid Philosophy: {philosophy_title}</title>
        </head>
        <body style="margin:0;padding:0;background-color:#f8f9fa;font-family:Arial,Helvetica,sans-serif;">
            <div style="max-width:600px;margin:0 auto;background-color:#ffffff;border-radius:8px;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                
                <!-- Header with Logo -->
                <div style="text-align:center;padding:30px 20px 20px 20px;background:linear-gradient(135deg, #2b6a30 0%, #1e4d23 100%);border-radius:8px 8px 0 0;">
                    <img src="{self.logo_url}" alt="Five Cities Orchid Society Logo" style="max-width:180px;height:auto;margin-bottom:15px;">
                    <h1 style="color:#ffffff;font-size:28px;margin:0;font-weight:300;">Your Orchid Philosophy</h1>
                </div>
                
                <!-- Main Content -->
                <div style="padding:40px 30px;">
                    
                    <!-- Philosophy Title -->
                    <h2 style="text-align:center;color:#2b6a30;font-size:32px;margin:0 0 20px 0;font-weight:bold;">{philosophy_title}</h2>
                    
                    <!-- Badge Display -->
                    <div style="text-align:center;margin:25px 0;">
                        <a href="{phil_data['badge_link']}" target="_blank" style="text-decoration:none;">
                            <div style="display:inline-block;padding:20px;background:linear-gradient(45deg, #f8f9fa, #e9ecef);border-radius:12px;border:3px solid #2b6a30;">
                                <div style="font-size:48px;margin-bottom:10px;">🌺</div>
                                <div style="color:#2b6a30;font-weight:bold;font-size:16px;">Click to View Your Badge</div>
                            </div>
                        </a>
                    </div>
                    
                    <!-- Personal Greeting -->
                    <p style="font-size:18px;color:#333;line-height:1.6;">Hi {safe_name},</p>
                    
                    <p style="font-size:18px;color:#333;line-height:1.6;"><strong>{philosophy_title}</strong> reflects how you meet the world—and how you meet your orchids.</p>
                    
                    <!-- Life Philosophy Section -->
                    <div style="margin:30px 0;padding:25px;background-color:#f8f9fa;border-left:4px solid #2b6a30;border-radius:0 8px 8px 0;">
                        <h3 style="color:#2b6a30;font-size:22px;margin:0 0 15px 0;">Your Life Philosophy</h3>
                        <p style="font-size:16px;color:#444;line-height:1.7;margin:0;">{phil_data['life_philosophy']}</p>
                    </div>
                    
                    <!-- Orchid Reflection Section -->
                    <div style="margin:30px 0;padding:25px;background-color:#f0f8f0;border-left:4px solid #4a7c59;border-radius:0 8px 8px 0;">
                        <h3 style="color:#2b6a30;font-size:22px;margin:0 0 15px 0;">Orchid Reflection</h3>
                        <p style="font-size:16px;color:#444;line-height:1.7;margin:0;">{phil_data['orchid_reflection']}</p>
                    </div>
                    
                    <!-- Poetic Reflection Section -->
                    <div style="text-align:center;margin:35px 0;padding:30px;background:linear-gradient(135deg, #e8f5e8, #f0f8f0);border-radius:12px;border:1px solid #d4e6d4;">
                        <div style="font-family:'Brush Script MT','Segoe Script','Apple Chancery',cursive;font-size:24px;color:#1e4d23;line-height:1.8;font-style:italic;">
                            {phil_data['haiku'].replace(chr(10), '<br>')}
                        </div>
                    </div>
                    
                    <!-- Practical Tip -->
                    <div style="margin:30px 0;">
                        <h3 style="color:#2b6a30;font-size:20px;margin:0 0 10px 0;">🌱 Practical Growing Tip</h3>
                        <p style="font-size:16px;color:#444;line-height:1.7;margin:0;padding:15px;background-color:#fff9e6;border-radius:8px;border-left:3px solid #ffc107;">{phil_data['practical']}</p>
                    </div>
                    
                    <!-- Science Fact -->
                    <div style="margin:30px 0;">
                        <h3 style="color:#2b6a30;font-size:20px;margin:0 0 10px 0;">🔬 Botanical Science Fact</h3>
                        <p style="font-size:16px;color:#444;line-height:1.7;margin:0;padding:15px;background-color:#e6f3ff;border-radius:8px;border-left:3px solid #0066cc;">{phil_data['science']}</p>
                    </div>
                    
                    <!-- Social Sharing & CTAs -->
                    <div style="margin:40px 0;text-align:center;padding:30px;background-color:#f8f9fa;border-radius:12px;">
                        <h3 style="color:#2b6a30;font-size:22px;margin:0 0 20px 0;">Share Your Result & Join Our Community</h3>
                        
                        <!-- Social Share Buttons -->
                        <div style="margin:20px 0;">
                            <a href="https://www.facebook.com/sharer/sharer.php?u=https://fcos.org/philosophy-quiz" target="_blank" style="display:inline-block;margin:5px;padding:10px 20px;background-color:#4267B2;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">📘 Share on Facebook</a>
                            <a href="https://twitter.com/intent/tweet?text=I just discovered my Orchid Philosophy: {philosophy_title}! Take the quiz at https://fcos.org/philosophy-quiz" target="_blank" style="display:inline-block;margin:5px;padding:10px 20px;background-color:#1DA1F2;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">🐦 Share on Twitter</a>
                        </div>
                        
                        <!-- CTA Buttons -->
                        <div style="margin:25px 0;">
                            <a href="https://fivecitiesorchidsociety.app.neoncrm.com/forms/12" target="_blank" style="display:inline-block;margin:8px;padding:12px 25px;background-color:#2b6a30;color:white;text-decoration:none;border-radius:8px;font-weight:bold;font-size:16px;">🌿 Join Our Society</a>
                            <a href="https://fivecitiesorchidsociety.app.neoncrm.com/subscribe.jsp?subscription=6" target="_blank" style="display:inline-block;margin:8px;padding:12px 25px;background-color:#4a7c59;color:white;text-decoration:none;border-radius:8px;font-weight:bold;font-size:16px;">📰 Free Newsletter</a>
                            <a href="https://www.fcos.org" target="_blank" style="display:inline-block;margin:8px;padding:12px 25px;background-color:#6c757d;color:white;text-decoration:none;border-radius:8px;font-weight:bold;font-size:16px;">🏡 Visit Website</a>
                        </div>
                        
                        <!-- Refer a Friend -->
                        <div style="margin:25px 0;padding:20px;background-color:#fff;border-radius:8px;border:2px dashed #2b6a30;">
                            <p style="margin:0 0 10px 0;font-size:16px;color:#333;"><strong>💝 Invite a Friend to Take the Quiz!</strong></p>
                            <a href="https://forms.gle/nAr2wthXzCgMdWFB9" target="_blank" style="display:inline-block;padding:10px 20px;background-color:#ff6b6b;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">🎯 Share the Quiz</a>
                        </div>
                    </div>
                    
                </div>
                
                <!-- Footer -->
                <div style="padding:30px;background-color:#2b6a30;color:#ffffff;text-align:center;border-radius:0 0 8px 8px;">
                    <p style="margin:0 0 15px 0;font-size:16px;"><em>Established in 1990, the Five Cities Orchid Society is a 501(c)(3) nonprofit dedicated to promoting the love, knowledge, and conservation of orchids for growers of all levels.</em></p>
                    
                    <p style="margin:0;font-size:16px;"><strong>Five Cities Orchid Society</strong><br>
                    <a href="https://www.fcos.org" style="color:#b8e6c1;">www.fcos.org</a></p>
                    
                    <!-- Unsubscribe Link -->
                    <p style="margin:20px 0 0 0;font-size:12px;color:#b8e6c1;">
                        <a href="[unsubscribe]" style="color:#b8e6c1;">Unsubscribe</a> | 
                        <a href="mailto:info@fcos.org" style="color:#b8e6c1;">Contact Us</a>
                    </p>
                </div>
                
            </div>
        </body>
        </html>
        """

# Function to send philosophy result (can be imported and used elsewhere)
def send_philosophy_result_email(user_email, user_name, philosophy_result):
    """Main function to send philosophy result email"""
    emailer = PhilosophyQuizEmailer()
    return emailer.send_philosophy_result_email(user_email, user_name, philosophy_result)