class Throttler:
    
    LIMITS = {
        'free': {
            'reports_per_month': 1,
            'sites': 1,
            'email_scheduling': False,
            'white_label': False,
            'api_access': False,
            'users': 1
        },
        'starter': {
            'reports_per_month': 50,
            'sites': 3,
            'email_scheduling': False,
            'white_label': False,
            'api_access': False,
            'users': 1
        },
        'premium': {
            'reports_per_month': 999999,  # unlimited
            'sites': 20,
            'email_scheduling': True,
            'white_label': False,
            'api_access': False,
            'users': 3
        },
        'enterprise': {
            'reports_per_month': 999999,  # unlimited
            'sites': 999999,  # unlimited
            'email_scheduling': True,
            'white_label': True,
            'api_access': True,
            'users': 999999  # unlimited
        }
    }
    
    @staticmethod
    def get_limits(tier):
        return Throttler.LIMITS.get(tier, Throttler.LIMITS['free'])
    
    @staticmethod
    def can_generate_report(user):
        tier = user['tier']
        limits = Throttler.get_limits(tier)
        
        # Check report limit
        if user['reports_used'] >= limits['reports_per_month']:
            return False, f"You've reached your monthly limit of {limits['reports_per_month']} reports. Upgrade to generate more reports."
        
        return True, None
    
    @staticmethod
    def can_add_site(user, site_url, supabase):
        tier = user['tier']
        limits = Throttler.get_limits(tier)
        
        # Check if site already exists
        existing_site = supabase.table('sites').select('*').eq('user_id', user['id']).eq('url', site_url).execute()
        
        if existing_site.data:
            return True, None  # Site already added
        
        # Count user's sites
        sites_count = len(supabase.table('sites').select('*').eq('user_id', user['id']).execute().data)
        
        if sites_count >= limits['sites']:
            return False, f"You've reached your limit of {limits['sites']} sites. Upgrade to add more sites."
        
        # Add site
        supabase.table('sites').insert({
            'user_id': user['id'],
            'url': site_url
        }).execute()
        
        # Update user's site count
        supabase.table('users').update({
            'sites_used': sites_count + 1
        }).eq('id', user['id']).execute()
        
        return True, None
    
    @staticmethod
    def get_usage_percentage(user):
        tier = user['tier']
        limits = Throttler.get_limits(tier)
        
        if limits['reports_per_month'] == 999999:
            return 0  # unlimited
        
        percentage = (user['reports_used'] / limits['reports_per_month']) * 100
        return min(percentage, 100)
    
    @staticmethod
    def should_show_upgrade_modal(user):
        tier = user['tier']
        limits = Throttler.get_limits(tier)
        
        # Show modal at 80% usage or when limit is reached
        if tier == 'free':
            return user['reports_used'] >= limits['reports_per_month']
        
        usage_percentage = Throttler.get_usage_percentage(user)
        return usage_percentage >= 80
    
    @staticmethod
    def get_recommended_tier(user):
        if user['tier'] == 'free':
            return 'starter'
        elif user['tier'] == 'starter':
            return 'premium'
        elif user['tier'] == 'premium':
            return 'enterprise'
        return None
