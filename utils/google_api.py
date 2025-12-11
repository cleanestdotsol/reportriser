import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import requests

class GoogleAPIClient:
    SCOPES = [
        'https://www.googleapis.com/auth/analytics.readonly',
        'https://www.googleapis.com/auth/webmasters.readonly'
    ]
    
    @staticmethod
    def get_auth_url(user_id):
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                    "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [os.getenv('GOOGLE_REDIRECT_URI')]
                }
            },
            scopes=GoogleAPIClient.SCOPES,
            redirect_uri=os.getenv('GOOGLE_REDIRECT_URI')
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=user_id,
            prompt='consent'
        )
        
        return auth_url
    
    @staticmethod
    def exchange_code(code):
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                    "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [os.getenv('GOOGLE_REDIRECT_URI')]
                }
            },
            scopes=GoogleAPIClient.SCOPES,
            redirect_uri=os.getenv('GOOGLE_REDIRECT_URI')
        )
        
        flow.fetch_token(code=code)
        return flow.credentials.to_json()
    
    def __init__(self, user_id, supabase):
        self.user_id = user_id
        self.supabase = supabase
        self.credentials = self._get_credentials()
    
    def _get_credentials(self):
        token_data = self.supabase.table('google_tokens').select('*').eq('user_id', self.user_id).execute()
        
        if not token_data.data:
            raise Exception("No Google tokens found")
        
        token = token_data.data[0]
        
        creds = Credentials(
            token=token['access_token'],
            refresh_token=token['refresh_token'],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
        )
        
        # Refresh if expired
        if datetime.fromisoformat(token['expires_at']) < datetime.now():
            creds.refresh(requests.Request())
            
            self.supabase.table('google_tokens').update({
                'access_token': creds.token,
                'expires_at': (datetime.now() + timedelta(seconds=3600)).isoformat()
            }).eq('user_id', self.user_id).execute()
        
        return creds
    
    def get_analytics_data(self, site_url):
        try:
            service = build('analyticsdata', 'v1beta', credentials=self.credentials)
            
            # Get property ID (simplified - in production, store this per site)
            property_id = 'properties/YOUR_PROPERTY_ID'
            
            response = service.properties().runReport(
                property=property_id,
                body={
                    'dateRanges': [{'startDate': '30daysAgo', 'endDate': 'today'}],
                    'dimensions': [{'name': 'date'}],
                    'metrics': [{'name': 'activeUsers'}]
                }
            ).execute()
            
            # Parse response
            traffic_data = []
            total_users = 0
            
            for row in response.get('rows', []):
                date = row['dimensionValues'][0]['value']
                users = int(row['metricValues'][0]['value'])
                traffic_data.append({'date': date, 'users': users})
                total_users += users
            
            return {
                'total_users': total_users,
                'traffic_data': traffic_data
            }
        except Exception as e:
            print(f"Analytics error: {e}")
            raise
    
    def get_search_console_data(self, site_url):
        try:
            service = build('searchconsole', 'v1', credentials=self.credentials)
            
            response = service.searchanalytics().query(
                siteUrl=site_url,
                body={
                    'startDate': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'endDate': datetime.now().strftime('%Y-%m-%d'),
                    'dimensions': ['query', 'page'],
                    'rowLimit': 10
                }
            ).execute()
            
            top_keywords = []
            top_pages = []
            
            for row in response.get('rows', [])[:5]:
                top_keywords.append({
                    'keyword': row['keys'][0],
                    'clicks': row['clicks'],
                    'impressions': row['impressions'],
                    'ctr': round(row['ctr'] * 100, 2),
                    'position': round(row['position'], 1)
                })
            
            for row in response.get('rows', [])[:10]:
                if len(row['keys']) > 1:
                    top_pages.append({
                        'page': row['keys'][1],
                        'clicks': row['clicks']
                    })
            
            return {
                'top_keywords': top_keywords,
                'top_pages': top_pages[:10]
            }
        except Exception as e:
            print(f"Search Console error: {e}")
            raise
    
    def get_pagespeed_data(self, site_url):
        try:
            api_key = os.getenv('GOOGLE_PAGESPEED_API_KEY')
            url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={site_url}&key={api_key}"
            
            response = requests.get(url).json()
            
            lighthouse = response['lighthouseResult']['categories']
            
            return {
                'performance': int(lighthouse['performance']['score'] * 100),
                'accessibility': int(lighthouse['accessibility']['score'] * 100),
                'best_practices': int(lighthouse['best-practices']['score'] * 100),
                'seo': int(lighthouse['seo']['score'] * 100)
            }
        except Exception as e:
            print(f"PageSpeed error: {e}")
            raise
