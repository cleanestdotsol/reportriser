# At the TOP of the file, before any other imports
import os
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

# Force matplotlib to use non-GUI backend


from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
from datetime import datetime
import os
import tempfile
from utils.roi_calculator import ROICalculator

# Charts disabled on serverless
CHARTS_ENABLED = False


class ReportGenerator:
    
    @staticmethod
    def get_mock_analytics():
        return {
            'total_users': 12543,
            'traffic_data': [
                {'date': f'2024-12-{i:02d}', 'users': 400 + (i * 10)} 
                for i in range(1, 31)
            ]
        }
    
    @staticmethod
    def get_mock_search_data():
        return {
            'top_keywords': [
                {'keyword': 'best seo tools', 'clicks': 1250, 'impressions': 15000, 'ctr': 8.3, 'position': 3.2},
                {'keyword': 'seo reporting', 'clicks': 890, 'impressions': 12000, 'ctr': 7.4, 'position': 4.1},
                {'keyword': 'automated seo', 'clicks': 650, 'impressions': 9500, 'ctr': 6.8, 'position': 5.3},
                {'keyword': 'seo analytics', 'clicks': 520, 'impressions': 8000, 'ctr': 6.5, 'position': 6.1},
                {'keyword': 'white label seo', 'clicks': 380, 'impressions': 6200, 'ctr': 6.1, 'position': 7.8}
            ],
            'top_pages': [
                {'page': '/blog/seo-guide', 'clicks': 2340},
                {'page': '/pricing', 'clicks': 1890},
                {'page': '/features', 'clicks': 1560},
                {'page': '/blog/keyword-research', 'clicks': 1230},
                {'page': '/case-studies', 'clicks': 980},
                {'page': '/blog/technical-seo', 'clicks': 870},
                {'page': '/integrations', 'clicks': 750},
                {'page': '/blog/link-building', 'clicks': 640},
                {'page': '/about', 'clicks': 520},
                {'page': '/contact', 'clicks': 410}
            ]
        }
    
    @staticmethod
    def get_mock_pagespeed():
        return {
            'performance': 87,
            'accessibility': 93,
            'best_practices': 90,
            'seo': 95
        }
    
    @staticmethod
    def generate_charts(analytics_data, search_data):
        """Charts disabled for serverless deployment"""
        return {'traffic': None, 'pages': None, 'keywords': None}
    
    @staticmethod
    def generate_pdf(site_url, analytics_data, search_data, cwv_summary, roi_data, conversions_data, tier):
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        import tempfile
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=30,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=12,
            spaceBefore=20
        )
        
        # Title
        if tier != 'enterprise':
            story.append(Paragraph("SEO Performance Report", title_style))
        else:
            story.append(Paragraph("Custom SEO Analytics Report", title_style))
        
        story.append(Paragraph(f"<b>Domain:</b> {site_url}", styles['Normal']))
        story.append(Paragraph(f"<b>Report Date:</b> {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # ===== NEW: ROI SUMMARY SECTION =====
        story.append(Paragraph("Organic ROI Summary", heading_style))
        
        roi_growth = ROICalculator.calculate_growth(
            conversions_data['conversion_value'],
            conversions_data['previous_value']
        )
        
        roi_text = f"""
        <b>{analytics_data['total_users']:,} organic visitors</b> generated 
        <b>{conversions_data['conversions']} conversions</b> this month, resulting in 
        <b>{ROICalculator.format_currency(roi_data['revenue'])} in revenue</b> 
        ({'+' if roi_growth > 0 else ''}{roi_growth}% vs last month).
        <br/><br/>
        <b>Conversion Rate:</b> {roi_data['conversion_rate']}% | 
        <b>Avg Order Value:</b> ${conversions_data['conversion_value'] / conversions_data['conversions']:.0f}
        """
        story.append(Paragraph(roi_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # ===== NEW: CORE WEB VITALS SECTION =====
        story.append(Paragraph("Core Web Vitals Assessment", heading_style))
        
        cwv_data = [
            ['Metric', 'Value', 'Status', 'Impact'],
            [
                'LCP (Load Speed)', 
                f"{cwv_summary['metrics']['lcp']['value']}s",
                f"{cwv_summary['metrics']['lcp']['icon']} {cwv_summary['metrics']['lcp']['status'].replace('_', ' ').title()}",
                'Load time affects conversions'
            ],
            [
                'FID (Interactivity)', 
                f"{cwv_summary['metrics']['fid']['value']}ms",
                f"{cwv_summary['metrics']['fid']['icon']} {cwv_summary['metrics']['fid']['status'].replace('_', ' ').title()}",
                'Response time affects engagement'
            ],
            [
                'CLS (Visual Stability)', 
                f"{cwv_summary['metrics']['cls']['value']}",
                f"{cwv_summary['metrics']['cls']['icon']} {cwv_summary['metrics']['cls']['status'].replace('_', ' ').title()}",
                'Layout shifts hurt UX'
            ]
        ]
        
        cwv_table = Table(cwv_data, colWidths=[1.8*inch, 1*inch, 1.8*inch, 1.6*inch])
        cwv_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        
        story.append(cwv_table)
        story.append(Spacer(1, 0.15*inch))
        
        # CWV Score and Recommendation
        cwv_score_text = f"""
        <b>Overall CWV Score: {cwv_summary['score']}/100</b><br/>
        <i>{cwv_summary['overall_recommendation']}</i>
        """
        story.append(Paragraph(cwv_score_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Priority Fix with detailed recommendation
        priority_metric = None
        for metric_key, metric_data in cwv_summary['metrics'].items():
            if metric_data['status'] in ['poor', 'needs_improvement']:
                priority_metric = metric_data
                break
        
        if priority_metric:
            fix_text = f"<b>Priority Fix:</b> {priority_metric['recommendation']}"
            story.append(Paragraph(fix_text, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Original PageSpeed Scores (keep existing)
        story.append(Paragraph("Additional Performance Metrics", heading_style))
        # ... keep your existing pagespeed table code ...
        
        # Generate and add charts (keep existing chart code)
        charts = ReportGenerator.generate_charts(analytics_data, search_data)
        
        story.append(PageBreak())
        
        # Traffic Summary (instead of chart)
        story.append(PageBreak())
        story.append(Paragraph("Traffic Analysis", heading_style))

        traffic_summary = f"""
        Over the past 30 days, your site received <b>{analytics_data['total_users']:,} organic visitors</b>.
        <br/><br/>
        <b>Peak traffic day:</b> {max(analytics_data['traffic_data'], key=lambda x: x['users'])['date']} 
        ({max(analytics_data['traffic_data'], key=lambda x: x['users'])['users']} users)
        <br/>
        <b>Average daily visitors:</b> {analytics_data['total_users'] // 30:,}
        """
        story.append(Paragraph(traffic_summary, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))

        # Top Pages Summary (instead of chart)
        story.append(Paragraph("Top Performing Pages", heading_style))

        pages_data = [['Page', 'Clicks', '% of Total']]
        total_clicks = sum([p['clicks'] for p in search_data['top_pages']])
        for page in search_data['top_pages'][:10]:
            percent = round((page['clicks'] / total_clicks * 100), 1)
            pages_data.append([page['page'], f"{page['clicks']:,}", f"{percent}%"])

        pages_table = Table(pages_data, colWidths=[3.5*inch, 1.5*inch, 1.2*inch])
        pages_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))

        story.append(pages_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Keywords table (keep existing)
        story.append(Paragraph("Top Keywords Details", heading_style))
        keywords_data = [['Keyword', 'Clicks', 'Impressions', 'CTR', 'Position']]
        for kw in search_data['top_keywords']:
            keywords_data.append([
                kw['keyword'],
                str(kw['clicks']),
                str(kw['impressions']),
                f"{kw['ctr']}%",
                str(kw['position'])
            ])
        
        keywords_table = Table(keywords_data, colWidths=[2.2*inch, 1*inch, 1.2*inch, 0.8*inch, 1*inch])
        keywords_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(keywords_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Watermark for non-enterprise
        if tier != 'enterprise':
            story.append(Paragraph(
                "<i>Generated by ReportRiser.com — Prove SEO ROI in 60 Seconds</i>", 
                ParagraphStyle('footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1)
            ))
        
        doc.build(story)
        
        return filepath

