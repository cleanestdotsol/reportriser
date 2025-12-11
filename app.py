from utils.roi_calculator import ROICalculator
from utils.cwv import CWVAnalyzer
from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import os
from datetime import datetime, timedelta
import stripe
from supabase import create_client, Client
from utils.google_api import GoogleAPIClient
from utils.report_generator import ReportGenerator
from utils.email_sender import EmailSender
from utils.throttler import Throttler
import hashlib
import secrets

from dotenv import load_dotenv
load_dotenv()  # Load .env file

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Initialize services
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

PRICING = {
    'starter_monthly': {'price_id': os.getenv('STRIPE_STARTER_MONTHLY'), 'amount': 3900},
    'starter_yearly': {'price_id': os.getenv('STRIPE_STARTER_YEARLY'), 'amount': 2900},
    'premium_monthly': {'price_id': os.getenv('STRIPE_PREMIUM_MONTHLY'), 'amount': 8900},
    'premium_yearly': {'price_id': os.getenv('STRIPE_PREMIUM_YEARLY'), 'amount': 6900},
    'enterprise_monthly': {'price_id': os.getenv('STRIPE_ENTERPRISE_MONTHLY'), 'amount': 24900},
    'enterprise_yearly': {'price_id': os.getenv('STRIPE_ENTERPRISE_YEARLY'), 'amount': 19900},
}

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/test-login')
def test_login():
    # Quick test login - bypasses email verification
    session['user_id'] = 'test-user-123'
    session['email'] = 'test@example.com'
    session['tier'] = 'free'
    return redirect('/dashboard')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    
    # Generate magic link token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=1)
    
    # Store token in Supabase
    supabase.table('magic_links').insert({
        'email': email,
        'token': token,
        'expires_at': expires_at.isoformat()
    }).execute()
    
    # Send email
    magic_link = f"https://reportriser.com/verify?token={token}"
    EmailSender.send_magic_link(email, magic_link)
    
    return jsonify({'success': True, 'message': 'Check your email for login link'})

@app.route('/verify')
def verify():
    token = request.args.get('token')
    
    # Verify token
    result = supabase.table('magic_links').select('*').eq('token', token).execute()
    
    if not result.data or datetime.fromisoformat(result.data[0]['expires_at']) < datetime.now():
        return "Invalid or expired link", 400
    
    email = result.data[0]['email']
    
    # Get or create user
    user_result = supabase.table('users').select('*').eq('email', email).execute()
    
    if not user_result.data:
        user_result = supabase.table('users').insert({
            'email': email,
            'tier': 'free',
            'reports_used': 0,
            'sites_used': 0
        }).execute()
    
    user = user_result.data[0]
    session['user_id'] = user['id']
    session['email'] = user['email']
    session['tier'] = user['tier']
    
    # Delete used token
    supabase.table('magic_links').delete().eq('token', token).execute()
    
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    
    # Handle mock user
    if session.get('user_id') == 'mock-user':
        user = {
            'id': 'mock-user',
            'email': session.get('email', 'test@example.com'),
            'tier': session.get('tier', 'free'),
            'reports_used': 0,
            'sites_used': 0,
            'stripe_customer_id': None
        }
        reports = []
    else:
        try:
            user = supabase.table('users').select('*').eq('id', session['user_id']).execute().data[0]
            reports = supabase.table('reports').select('*').eq('user_id', session['user_id']).order('created_at', desc=True).limit(10).execute().data
        except:
            user = {
                'id': session['user_id'],
                'email': session.get('email', 'test@example.com'),
                'tier': session.get('tier', 'free'),
                'reports_used': 0,
                'sites_used': 0,
                'stripe_customer_id': None
            }
            reports = []
    
    limits = {
        'reports_per_month': 1 if user['tier'] == 'free' else (50 if user['tier'] == 'starter' else 999999),
        'sites': 1 if user['tier'] == 'free' else (3 if user['tier'] == 'starter' else 999999)
    }
    
    # Calculate total ROI from reports (mock for now)
    total_roi = sum([r.get('roi', 0) for r in reports]) if reports else 4500
    
    return render_template('dashboard.html', 
                          user=user, 
                          reports=reports, 
                          limits=limits,
                          total_roi=total_roi)

@app.route('/google-auth')
def google_auth():
    if 'user_id' not in session:
        return redirect('/')
    
    auth_url = GoogleAPIClient.get_auth_url(session['user_id'])
    return redirect(auth_url)

@app.route('/google-callback')
def google_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    
    tokens = GoogleAPIClient.exchange_code(code)
    
    # Store tokens
    supabase.table('google_tokens').upsert({
        'user_id': state,
        'access_token': tokens['access_token'],
        'refresh_token': tokens.get('refresh_token'),
        'expires_at': (datetime.now() + timedelta(seconds=tokens['expires_in'])).isoformat()
    }).execute()
    
    return redirect('/dashboard?connected=true')

@app.route('/generate-report', methods=['POST'])
def generate_report():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    site_url = request.form.get('site_url')
    avg_order_value = float(request.form.get('avg_order_value', 100))
    
    try:
        from utils.report_generator import ReportGenerator
        
        print(f"📊 Generating report for: {site_url}")
        
        # Get analytics data (mock or real)
        analytics_data = ReportGenerator.get_mock_analytics()
        search_data = ReportGenerator.get_mock_search_data()
        
        # Get CWV data
        cwv_data = CWVAnalyzer.get_cwv_data(site_url)
        cwv_summary = CWVAnalyzer.get_cwv_summary(cwv_data)
        
        # Get conversion/ROI data
        conversions_data = ROICalculator.get_mock_conversions()
        roi_data = ROICalculator.get_roi_summary(
            analytics_data['total_users'], 
            conversions_data['conversions'],
            avg_order_value
        )
        
        print("✅ Data loaded (traffic, CWV, ROI)")
        
        # Generate PDF with enhanced data
        pdf_path = ReportGenerator.generate_pdf(
            site_url,
            analytics_data,
            search_data,
            cwv_summary,
            roi_data,
            conversions_data,
            session.get('tier', 'free')
        )
        
        print(f"✅ PDF generated at: {pdf_path}")
        
        import time
        report_id = f"report_{int(time.time())}"
        session[f'report_{report_id}'] = pdf_path
        
        return jsonify({'success': True, 'report_id': report_id})
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/download-report/<report_id>')
def download_report(report_id):
    if 'user_id' not in session:
        return redirect('/')
    
    # Get PDF path from session
    pdf_path = session.get(f'report_{report_id}')
    
    if not pdf_path:
        return "Report not found. Try generating it again.", 404
    
    try:
        import os
        if not os.path.exists(pdf_path):
            return f"PDF file not found at: {pdf_path}", 404
            
        return send_file(pdf_path, as_attachment=True, download_name=f"seo-report-{report_id}.pdf")
    except Exception as e:
        print(f"❌ Download error: {e}")
        return f"Error downloading report: {str(e)}", 500

@app.route('/checkout', methods=['POST'])
def create_checkout():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    price_key = request.form.get('price_key')
    
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=session['email'],
            payment_method_types=['card'],
            line_items=[{
                'price': PRICING[price_key]['price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://reportriser.com/dashboard?payment=success',
            cancel_url='https://reportriser.com/dashboard?payment=cancelled',
            client_reference_id=session['user_id']
        )
        
        return jsonify({'url': checkout_session.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        user_id = session_obj['client_reference_id']
        
        # Get subscription details
        subscription = stripe.Subscription.retrieve(session_obj['subscription'])
        price_id = subscription['items']['data'][0]['price']['id']
        
        # Determine tier
        tier = 'starter'
        for key, val in PRICING.items():
            if val['price_id'] == price_id:
                if 'premium' in key:
                    tier = 'premium'
                elif 'enterprise' in key:
                    tier = 'enterprise'
                break
        
        # Update user
        supabase.table('users').update({
            'tier': tier,
            'stripe_customer_id': session_obj['customer'],
            'stripe_subscription_id': session_obj['subscription']
        }).eq('id', user_id).execute()
        
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        
        # Downgrade to free
        supabase.table('users').update({
            'tier': 'free'
        }).eq('stripe_subscription_id', subscription['id']).execute()
    
    return jsonify({'success': True})

@app.route('/audit')
def public_audit():
    """Public SEO audit tool - no login required"""
    site_url = request.args.get('url', '')
    
    if not site_url:
        return render_template('audit.html', audit_data=None)
    
    try:
        # Get CWV data
        cwv_data = CWVAnalyzer.get_cwv_data(site_url)
        cwv_summary = CWVAnalyzer.get_cwv_summary(cwv_data)
        
        # Basic on-page SEO check
        import requests
        from bs4 import BeautifulSoup
        
        try:
            response = requests.get(site_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract SEO elements
            title = soup.find('title')
            title_text = title.text if title else ''
            title_length = len(title_text)
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_desc_text = meta_desc['content'] if meta_desc and meta_desc.get('content') else ''
            meta_desc_length = len(meta_desc_text)
            
            h1_tags = soup.find_all('h1')
            h1_count = len(h1_tags)
            
            images = soup.find_all('img')
            images_without_alt = len([img for img in images if not img.get('alt')])
            missing_alt_percent = round((images_without_alt / len(images) * 100), 1) if images else 0
            
            seo_checks = {
                'title_length': title_length,
                'title_status': 'good' if 30 <= title_length <= 60 else 'warning',
                'meta_desc_length': meta_desc_length,
                'meta_desc_status': 'good' if 120 <= meta_desc_length <= 160 else 'warning',
                'h1_count': h1_count,
                'h1_status': 'good' if h1_count == 1 else 'warning',
                'missing_alt_percent': missing_alt_percent,
                'alt_status': 'good' if missing_alt_percent < 10 else 'warning'
            }
        except:
            seo_checks = None
        
        audit_data = {
            'url': site_url,
            'cwv': cwv_summary,
            'seo': seo_checks,
            'timestamp': datetime.now().strftime('%B %d, %Y at %I:%M %p')
        }
        
        return render_template('audit.html', audit_data=audit_data)
        
    except Exception as e:
        print(f"Audit error: {e}")
        return render_template('audit.html', audit_data={'error': str(e)})

@app.route('/demo')
def demo_report():
    """Demo page showing full Premium report with mock data"""
    
    # Generate demo data for nike.com
    demo_site = 'nike.com'
    
    analytics_data = {
        'total_users': 45230,
        'traffic_data': [
            {'date': f'2024-12-{i:02d}', 'users': 1400 + (i * 25)} 
            for i in range(1, 31)
        ]
    }
    
    search_data = {
        'top_keywords': [
            {'keyword': 'running shoes', 'clicks': 8250, 'impressions': 95000, 'ctr': 8.7, 'position': 2.1},
            {'keyword': 'nike air max', 'clicks': 6890, 'impressions': 82000, 'ctr': 8.4, 'position': 2.8},
            {'keyword': 'athletic wear', 'clicks': 5650, 'impressions': 71000, 'ctr': 8.0, 'position': 3.2},
            {'keyword': 'sports shoes', 'clicks': 4520, 'impressions': 63000, 'ctr': 7.2, 'position': 4.1},
            {'keyword': 'nike sneakers', 'clicks': 3380, 'impressions': 52000, 'ctr': 6.5, 'position': 5.3}
        ],
        'top_pages': [
            {'page': '/running-shoes', 'clicks': 12340},
            {'page': '/air-max-collection', 'clicks': 9890},
            {'page': '/mens-athletic-wear', 'clicks': 8560},
            {'page': '/womens-training', 'clicks': 7230},
            {'page': '/sale', 'clicks': 6980}
        ]
    }
    
    cwv_data = CWVAnalyzer.get_mock_cwv()
    cwv_summary = CWVAnalyzer.get_cwv_summary(cwv_data)
    
    conversions_data = ROICalculator.get_mock_conversions()
    roi_data = ROICalculator.get_roi_summary(analytics_data['total_users'], conversions_data['conversions'], 150)
    
    demo_data = {
        'site': demo_site,
        'traffic': analytics_data['total_users'],
        'conversions': conversions_data['conversions'],
        'roi': roi_data['revenue'],
        'conversion_rate': roi_data['conversion_rate'],
        'cwv_score': cwv_summary['score'],
        'top_keywords': search_data['top_keywords'][:3],
        'growth': '+18%'
    }
    
    return render_template('demo.html', demo=demo_data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)