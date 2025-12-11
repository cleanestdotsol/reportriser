import os
import resend

resend.api_key = os.getenv('RESEND_API_KEY')

class EmailSender:
    
    @staticmethod
    def send_magic_link(email, magic_link):
        try:
            params = {
                "from": "ReportRiser <auth@reportriser.com>",
                "to": [email],
                "subject": "Your ReportRiser Login Link",
                "html": f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .button {{ 
                            display: inline-block; 
                            padding: 12px 24px; 
                            background-color: #3b82f6; 
                            color: white; 
                            text-decoration: none; 
                            border-radius: 6px;
                            font-weight: bold;
                        }}
                        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Welcome to ReportRiser! 🚀</h2>
                        <p>Click the button below to log in to your account:</p>
                        <p style="margin: 30px 0;">
                            <a href="{magic_link}" class="button">Login to ReportRiser</a>
                        </p>
                        <p>This link expires in 1 hour.</p>
                        <p>If you didn't request this email, you can safely ignore it.</p>
                        <div class="footer">
                            <p>ReportRiser - Automated SEO Reporting<br>
                            <a href="https://reportriser.com">reportriser.com</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """
            }
            
            email_response = resend.Emails.send(params)
            return email_response
        except Exception as e:
            print(f"Email error: {e}")
            raise
    
    @staticmethod
    def send_report(email, site_url, pdf_path):
        try:
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            params = {
                "from": "ReportRiser <reports@reportriser.com>",
                "to": [email],
                "subject": f"Your SEO Report for {site_url}",
                "html": f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .stats {{ 
                            background: #f3f4f6; 
                            padding: 15px; 
                            border-radius: 8px; 
                            margin: 20px 0; 
                        }}
                        .button {{ 
                            display: inline-block; 
                            padding: 12px 24px; 
                            background-color: #10b981; 
                            color: white; 
                            text-decoration: none; 
                            border-radius: 6px;
                            font-weight: bold;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Your SEO Report is Ready! 📊</h2>
                        <p>We've generated your latest SEO report for <strong>{site_url}</strong>.</p>
                        <div class="stats">
                            <p><strong>Report Details:</strong></p>
                            <ul>
                                <li>Traffic analysis for the past 30 days</li>
                                <li>Top performing pages and keywords</li>
                                <li>Core Web Vitals scores</li>
                                <li>Actionable recommendations</li>
                            </ul>
                        </div>
                        <p>Your report is attached to this email. You can also view it anytime in your dashboard:</p>
                        <p style="margin: 20px 0;">
                            <a href="https://reportriser.com/dashboard" class="button">View Dashboard</a>
                        </p>
                        <p>Questions? Reply to this email or visit our help center.</p>
                    </div>
                </body>
                </html>
                """,
                "attachments": [{
                    "filename": f"seo-report-{site_url.replace('https://', '').replace('http://', '')}.pdf",
                    "content": pdf_content
                }]
            }
            
            email_response = resend.Emails.send(params)
            return email_response
        except Exception as e:
            print(f"Email error: {e}")
            raise
    
    @staticmethod
    def send_upgrade_notification(email, tier):
        try:
            params = {
                "from": "ReportRiser <hello@reportriser.com>",
                "to": [email],
                "subject": f"Welcome to ReportRiser {tier.capitalize()}! 🎉",
                "html": f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .badge {{ 
                            display: inline-block;
                            padding: 6px 12px;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border-radius: 20px;
                            font-weight: bold;
                            font-size: 14px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Thank you for upgrading! 🚀</h2>
                        <p>You're now on the <span class="badge">{tier.upper()}</span> plan.</p>
                        <p><strong>Your new features:</strong></p>
                        <ul>
                            {'<li>Unlimited reports</li>' if tier != 'starter' else '<li>50 reports per month</li>'}
                            {'<li>20 sites</li>' if tier == 'premium' else '<li>Unlimited sites</li>' if tier == 'enterprise' else '<li>3 sites</li>'}
                            {'<li>White-label reports</li>' if tier == 'enterprise' else ''}
                            {'<li>API access</li>' if tier == 'enterprise' else ''}
                            {'<li>Email scheduling</li>' if tier in ['premium', 'enterprise'] else ''}
                        </ul>
                        <p>Start creating reports now:</p>
                        <p><a href="https://reportriser.com/dashboard" style="color: #3b82f6;">Go to Dashboard →</a></p>
                    </div>
                </body>
                </html>
                """
            }
            
            return resend.Emails.send(params)
        except Exception as e:
            print(f"Email error: {e}")
            raise
