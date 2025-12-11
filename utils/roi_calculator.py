"""
ROI Calculator for organic traffic conversions
"""

class ROICalculator:
    
    @staticmethod
    def calculate_roi(conversions, avg_order_value=100):
        """Calculate revenue from organic conversions"""
        return conversions * avg_order_value
    
    @staticmethod
    def calculate_growth(current_value, previous_value):
        """Calculate percentage growth"""
        if previous_value == 0:
            return 0
        return round(((current_value - previous_value) / previous_value) * 100, 1)
    
    @staticmethod
    def get_ga4_conversions(google_client, site_url):
        """Pull conversions from GA4"""
        try:
            # This would use the google_client to fetch real GA4 data
            # For now returning structure for integration
            service = google_client.credentials  # Simplified
            
            # GA4 API call would go here
            # response = service.properties().runReport(...)
            
            return {
                'conversions': 45,
                'conversion_rate': 3.75,
                'previous_conversions': 38
            }
        except:
            return None
    
    @staticmethod
    def get_mock_conversions():
        """Mock conversion data for testing"""
        return {
            'conversions': 45,
            'conversion_rate': 3.75,
            'previous_conversions': 38,
            'conversion_value': 4500,
            'previous_value': 3800
        }
    
    @staticmethod
    def format_currency(amount):
        """Format number as currency"""
        return f"${amount:,.0f}"
    
    @staticmethod
    def get_roi_summary(organic_traffic, conversions, avg_order_value=100):
        """Generate ROI summary text"""
        revenue = ROICalculator.calculate_roi(conversions, avg_order_value)
        conversion_rate = (conversions / organic_traffic * 100) if organic_traffic > 0 else 0
        
        return {
            'revenue': revenue,
            'conversion_rate': round(conversion_rate, 2),
            'summary': f"{organic_traffic:,} organic visitors → {conversions} conversions → {ROICalculator.format_currency(revenue)} revenue"
        }
