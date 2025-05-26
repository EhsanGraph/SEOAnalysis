# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.views.generic import (
    TemplateView, CreateView, DetailView, ListView, 
    FormView, RedirectView
)
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.forms import ModelForm, URLField, CharField
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import json
import logging

from .models import SEOAnalysis

logger = logging.getLogger(__name__)

# Forms
class SEOAnalysisForm(ModelForm):
    url = URLField(
        max_length=500,
        widget=forms.URLInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'https://example.com',
            'required': True
        })
    )
    keyword = CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional: Target keyword'
        })
    )
    
    class Meta:
        model = SEOAnalysis
        fields = ['url', 'keyword']
    
    def clean_url(self):
        url = self.cleaned_data.get('url')
        if url:
            return self.normalize_url(url)
        return url
    
    def normalize_url(self, url):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValidationError('Invalid URL format')
        
        return url.lower().rstrip('/')


# Views
class HomeView(TemplateView):
    template_name = 'seo_analyzer/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form': SEOAnalysisForm(),
            'recent_analyses': self.get_recent_analyses(),
            'stats': self.get_dashboard_stats(),
        })
        return context
    
    def get_recent_analyses(self):
        return SEOAnalysis.objects.select_related().order_by('-created_at')[:5]
    
    def get_dashboard_stats(self):
        stats = SEOAnalysis.objects.aggregate(
            total_count=Count('id'),
            avg_score=Avg('seo_health_percentage'),
            critical_issues=Count('id', filter=Q(seo_health_percentage__lt=30)),
            good_scores=Count('id', filter=Q(seo_health_percentage__gte=80))
        )
        
        return {
            'total_analyses': stats['total_count'] or 0,
            'average_score': round(stats['avg_score'] or 0, 1),
            'critical_issues': stats['critical_issues'] or 0,
            'good_scores': stats['good_scores'] or 0
        }


class AnalyzeURLView(FormView):
    form_class = SEOAnalysisForm
    template_name = 'seo_analyzer/index.html'
    
    def form_valid(self, form):
        url = form.cleaned_data['url']
        keyword = form.cleaned_data.get('keyword', '')
        
        try:
            # Check if analysis exists and if reanalysis is needed
            analysis, created = SEOAnalysis.objects.get_or_create(
                url=url,
                defaults={'keyword': keyword}
            )
            
            if created or self.should_reanalyze(analysis):
                # Update keyword if provided
                if keyword and analysis.keyword != keyword:
                    analysis.keyword = keyword
                
                # Perform analysis
                success = self.perform_seo_analysis(analysis)
                
                if success:
                    analysis.save()  # This triggers all calculations
                    if created:
                        messages.success(self.request, 'Analysis completed successfully!')
                    else:
                        messages.success(self.request, 'Analysis updated successfully!')
                else:
                    if created:
                        analysis.delete()  # Clean up failed analysis
                    messages.error(self.request, 'Failed to analyze URL. Please check if the website is accessible.')
                    return self.form_invalid(form)
            else:
                messages.info(self.request, 'Using existing analysis (updated recently)')
            
            return redirect('seo_analyzer:analysis_detail', pk=analysis.pk)
            
        except Exception as e:
            logger.error(f"Analysis error for {url}: {str(e)}")
            messages.error(self.request, 'An error occurred during analysis. Please try again.')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def should_reanalyze(self, analysis):
        # Reanalyze if older than 24 hours
        return (datetime.now() - analysis.created_at.replace(tzinfo=None)).total_seconds() > 86400
    
    def perform_seo_analysis(self, analysis):
        try:
            # Fetch webpage content
            response = requests.get(
                analysis.url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                timeout=30,
                allow_redirects=True
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Basic SEO elements
            self.analyze_basic_elements(analysis, soup, response)
            
            # Content analysis
            self.analyze_content(analysis, soup)
            
            # Technical SEO
            self.analyze_technical_seo(analysis, soup, response)
            
            # Images
            self.analyze_images(analysis, soup)
            
            # Links
            self.analyze_links(analysis, soup)
            
            # Schema markup
            self.analyze_schema_markup(analysis, soup)
            
            return True
            
        except requests.RequestException as e:
            logger.error(f"Request failed for {analysis.url}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Analysis failed for {analysis.url}: {str(e)}")
            return False
    
    def analyze_basic_elements(self, analysis, soup, response):
        # Title
        title_tag = soup.find('title')
        analysis.title = title_tag.get_text().strip() if title_tag else ''
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            analysis.meta_description = meta_desc.get('content', '').strip()
        
        # Headers
        analysis.h1_count = len(soup.find_all('h1'))
        analysis.h2_count = len(soup.find_all('h2'))
        analysis.h3_count = len(soup.find_all('h3'))
        
        # H1 text
        h1_tag = soup.find('h1')
        analysis.h1_text = h1_tag.get_text().strip() if h1_tag else ''
        
        # H2 texts
        h2_tags = soup.find_all('h2')
        analysis.h2_texts = [h2.get_text().strip() for h2 in h2_tags]
        
        # HTTPS check
        analysis.https = analysis.url.startswith('https://')
    
    def analyze_content(self, analysis, soup):
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text_content = soup.get_text()
        words = re.findall(r'\b\w+\b', text_content.lower())
        analysis.word_count = len(words)
        
        # Keyword analysis
        if analysis.keyword:
            keyword_lower = analysis.keyword.lower()
            analysis.keyword_count = text_content.lower().count(keyword_lower)
        
        # Paragraph analysis
        paragraphs = soup.find_all('p')
        paragraph_data = []
        
        for p in paragraphs:
            p_text = p.get_text().strip()
            if p_text:  # Skip empty paragraphs
                paragraph_data.append({
                    'text': p_text,
                    'length': len(p_text)
                })
        
        analysis.paragraphs = paragraph_data
    
    def analyze_technical_seo(self, analysis, soup, response):
        # Canonical URL
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        analysis.has_canonical = canonical is not None
        
        # Mobile viewport
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        analysis.mobile_friendly = viewport is not None
        
        # Response time simulation (basic)
        analysis.page_load_time = response.elapsed.total_seconds()
    
    def analyze_images(self, analysis, soup):
        images = soup.find_all('img')
        analysis.images_count = len(images)
        
        missing_alt = 0
        for img in images:
            if not img.get('alt') or not img.get('alt').strip():
                missing_alt += 1
        
        analysis.missing_alt_images_count = missing_alt
    
    def analyze_links(self, analysis, soup):
        links = soup.find_all('a', href=True)
        internal_links = 0
        external_links = 0
        
        base_domain = urlparse(analysis.url).netloc
        
        for link in links:
            href = link.get('href', '')
            if href.startswith('http'):
                link_domain = urlparse(href).netloc
                if link_domain == base_domain:
                    internal_links += 1
                else:
                    external_links += 1
            elif href.startswith('/') or not href.startswith(('mailto:', 'tel:', '#')):
                internal_links += 1
        
        analysis.internal_links_count = internal_links
        analysis.external_links_count = external_links
    
    def analyze_schema_markup(self, analysis, soup):
        # Look for JSON-LD
        json_scripts = soup.find_all('script', type='application/ld+json')
        schema_types = []
        
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and '@type' in data:
                    schema_types.append(data['@type'])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and '@type' in item:
                            schema_types.append(item['@type'])
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Look for microdata
        microdata_items = soup.find_all(attrs={'itemtype': True})
        for item in microdata_items:
            itemtype = item.get('itemtype', '')
            if 'schema.org' in itemtype:
                schema_type = itemtype.split('/')[-1]
                schema_types.append(schema_type)
        
        analysis.has_schema_markup = len(schema_types) > 0
        analysis.schema_types = list(set(schema_types))  # Remove duplicates


class AnalysisDetailView(DetailView):
    model = SEOAnalysis
    template_name = 'seo_analyzer/analysis_detail.html'
    context_object_name = 'analysis'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analysis = self.get_object()
        
        context.update({
            'seo_grade': analysis.get_seo_grade(),
            'critical_recommendations': analysis.get_priority_recommendations('critical'),
            'high_recommendations': analysis.get_priority_recommendations('high'),
            'medium_recommendations': analysis.get_priority_recommendations('medium'),
            'low_recommendations': analysis.get_priority_recommendations('low'),
            'has_critical_errors': analysis.has_critical_errors(),
            'score_breakdown': self.get_score_breakdown(analysis),
        })
        return context
    
    def get_score_breakdown(self, analysis):
        return {
            'title': 8 if 50 <= analysis.title_length <= 60 else 4 if analysis.title_length > 0 else 0,
            'meta_description': 4 if 150 <= analysis.meta_description_length <= 160 else 0,
            'headers': 7 if analysis.h1_count == 1 and analysis.h2_count >= 2 else 3,
            'content': 14 if analysis.word_count >= 500 else 7 if analysis.word_count >= 300 else 0,
            'keywords': 20 if analysis.keyword and 1.0 <= analysis.keyword_density <= 2.5 else 10,
            'technical': 13 if analysis.https and analysis.has_canonical else 6,
            'images': 4 if analysis.missing_alt_images_count == 0 and analysis.images_count > 0 else 2,
            'schema': 4 if analysis.has_schema_markup else 0,
        }


class AnalysisListView(ListView):
    model = SEOAnalysis
    template_name = 'seo_analyzer/analysis_list.html'
    context_object_name = 'analyses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SEOAnalysis.objects.all().order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(url__icontains=search_query) |
                Q(title__icontains=search_query) |
                Q(keyword__icontains=search_query)
            )
        
        # Filter by score range
        score_filter = self.request.GET.get('score')
        if score_filter:
            if score_filter == 'excellent':
                queryset = queryset.filter(seo_health_percentage__gte=90)
            elif score_filter == 'good':
                queryset = queryset.filter(seo_health_percentage__range=(70, 89))
            elif score_filter == 'average':
                queryset = queryset.filter(seo_health_percentage__range=(50, 69))
            elif score_filter == 'poor':
                queryset = queryset.filter(seo_health_percentage__lt=50)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search_query': self.request.GET.get('search', ''),
            'score_filter': self.request.GET.get('score', ''),
            'total_count': self.get_queryset().count(),
        })
        return context


class CompareAnalysisView(TemplateView):
    template_name = 'seo_analyzer/compare.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get analysis IDs from query parameters
        ids = self.request.GET.getlist('ids')
        if ids:
            analyses = SEOAnalysis.objects.filter(id__in=ids)
            context['analyses'] = analyses
            context['comparison_data'] = self.prepare_comparison_data(analyses)
        else:
            context['all_analyses'] = SEOAnalysis.objects.all().order_by('-created_at')[:50]
        
        return context
    
    def prepare_comparison_data(self, analyses):
        comparison_data = {
            'labels': [analysis.url for analysis in analyses],
            'scores': [analysis.seo_health_percentage for analysis in analyses],
            'title_scores': [],
            'content_scores': [],
            'technical_scores': [],
        }
        
        for analysis in analyses:
            # Calculate individual component scores
            title_score = 100 if 50 <= analysis.title_length <= 60 else 50 if analysis.title_length > 0 else 0
            content_score = 100 if analysis.word_count >= 500 else 50 if analysis.word_count >= 300 else 0
            technical_score = 100 if analysis.https and analysis.has_canonical else 50
            
            comparison_data['title_scores'].append(title_score)
            comparison_data['content_scores'].append(content_score)
            comparison_data['technical_scores'].append(technical_score)
        
        return comparison_data


class DeleteAnalysisView(RedirectView):
    pattern_name = 'seo_analyzer:analysis_list'
    
    def get_redirect_url(self, *args, **kwargs):
        analysis_id = kwargs.get('pk')
        try:
            analysis = get_object_or_404(SEOAnalysis, pk=analysis_id)
            analysis.delete()
            messages.success(self.request, f'Analysis for {analysis.url} deleted successfully.')
        except Exception as e:
            messages.error(self.request, 'Failed to delete analysis.')
        
        return super().get_redirect_url(*args, **kwargs)


# API Views for AJAX requests
@method_decorator(csrf_exempt, name='dispatch')
class AnalysisAPIView(DetailView):
    model = SEOAnalysis
    
    def get(self, request, *args, **kwargs):
        try:
            analysis = self.get_object()
            data = {
                'id': analysis.id,
                'url': analysis.url,
                'title': analysis.title,
                'seo_health_percentage': analysis.seo_health_percentage,
                'seo_grade': analysis.get_seo_grade(),
                'word_count': analysis.word_count,
                'keyword': analysis.keyword,
                'keyword_density': analysis.keyword_density,
                'recommendations': analysis.recommendations,
                'created_at': analysis.created_at.isoformat(),
                'has_critical_errors': analysis.has_critical_errors(),
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class BulkAnalysisView(FormView):
    template_name = 'seo_analyzer/bulk_analysis.html'
    
    def post(self, request, *args, **kwargs):
        urls_text = request.POST.get('urls', '')
        keyword = request.POST.get('keyword', '')
        
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        if not urls:
            messages.error(request, 'Please provide URLs to analyze.')
            return self.get(request, *args, **kwargs)
        
        if len(urls) > 10:  # Limit bulk analysis
            messages.error(request, 'Maximum 10 URLs allowed for bulk analysis.')
            return self.get(request, *args, **kwargs)
        
        results = []
        for url in urls:
            try:
                # Normalize URL
                form = SEOAnalysisForm(data={'url': url, 'keyword': keyword})
                if form.is_valid():
                    normalized_url = form.cleaned_data['url']
                    
                    # Create or get analysis
                    analysis, created = SEOAnalysis.objects.get_or_create(
                        url=normalized_url,
                        defaults={'keyword': keyword}
                    )
                    
                    # Perform analysis if new or old
                    analyze_view = AnalyzeURLView()
                    if created or analyze_view.should_reanalyze(analysis):
                        success = analyze_view.perform_seo_analysis(analysis)
                        if success:
                            analysis.save()
                    
                    results.append({
                        'url': url,
                        'analysis': analysis,
                        'success': True
                    })
                else:
                    results.append({
                        'url': url,
                        'error': 'Invalid URL format',
                        'success': False
                    })
            except Exception as e:
                results.append({
                    'url': url,
                    'error': str(e),
                    'success': False
                })
        
        messages.success(request, f'Bulk analysis completed. Processed {len(results)} URLs.')
        return render(request, 'seo_analyzer/bulk_results.html', {'results': results})