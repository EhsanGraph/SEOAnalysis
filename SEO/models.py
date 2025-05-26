from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime, date
from typing import List, Dict, Any
import re

class SEOAnalysis(models.Model):
    url = models.URLField(unique=True, verbose_name="URL")
    
    # Basic fields
    title = models.CharField(max_length=255, blank=True, null=True)
    title_length = models.PositiveIntegerField(default=0)
    meta_description = models.TextField(blank=True, null=True)
    meta_description_length = models.PositiveIntegerField(default=0)
    
    # Header fields
    h1_count = models.PositiveIntegerField(default=0)
    h2_count = models.PositiveIntegerField(default=0)
    h3_count = models.PositiveIntegerField(default=0)
    h1_text = models.TextField(blank=True, null=True)
    h2_texts = models.JSONField(default=list)  # Stores all H2 texts as list
    
    # Content analysis
    word_count = models.PositiveIntegerField(default=0)
    keyword = models.CharField(max_length=100, blank=True, null=True)
    keyword_count = models.PositiveIntegerField(default=0)
    keyword_density = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    recommended_keyword_count = models.PositiveIntegerField(default=0)
    paragraphs = models.JSONField(default=list)  # Stores paragraph lengths
    
    # Media analysis
    images_count = models.PositiveIntegerField(default=0)
    missing_alt_images_count = models.PositiveIntegerField(default=0)
    
    # Technical SEO
    has_canonical = models.BooleanField(default=False)
    has_schema_markup = models.BooleanField(default=False)
    schema_types = models.JSONField(default=list)  # Stores schema types found
    internal_links_count = models.PositiveIntegerField(default=0)
    external_links_count = models.PositiveIntegerField(default=0)

    # Core Web Vitals
    largest_contentful_paint = models.FloatField(null=True, blank=True, verbose_name="LCP (ms)")
    first_input_delay = models.FloatField(null=True, blank=True, verbose_name="FID (ms)")
    cumulative_layout_shift = models.FloatField(null=True, blank=True, verbose_name="CLS")
    mobile_friendly = models.BooleanField(default=False)
    https = models.BooleanField(default=False)

    # Content Quality Signals
    content_readability_score = models.FloatField(null=True, blank=True)  # Flesch-Kincaid
    duplicate_content = models.BooleanField(default=False)
    thin_content = models.BooleanField(default=False)
    content_freshness = models.DateField(null=True, blank=True)
    semantic_keywords = models.JSONField(default=list)  # LSI keywords

    # Advanced Technical SEO
    robots_txt_status = models.BooleanField(default=False)
    sitemap_status = models.BooleanField(default=False)
    page_load_time = models.FloatField(null=True, blank=True)  # in seconds
    render_blocking_resources = models.JSONField(default=list)
    lazy_loading_images = models.BooleanField(default=False)

    # Enhanced Schema Markup Analysis
    schema_errors = models.JSONField(default=list)
    rich_snippet_opportunities = models.JSONField(default=list)
    faq_schema_present = models.BooleanField(default=False)
    breadcrumb_schema_present = models.BooleanField(default=False)

    # E-E-A-T Factors
    author_credentials = models.BooleanField(default=False)
    author_bylines = models.BooleanField(default=False)
    citation_sources = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(null=True, blank=True)
    contact_info_present = models.BooleanField(default=False)

    # Scoring
    seo_health_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Additional fields
    hreflang_implemented = models.BooleanField(default=False)
    image_compression_score = models.FloatField(null=True, blank=True)
    security_headers = models.JSONField(default=list)
    
    recommendations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Improved weight distribution (total = 100)
    SEO_WEIGHTS = {
        'title': 8,
        'meta_description': 4,
        'h1': 4,
        'headers_structure': 4,
        'headers_unique': 3,
        'images': 4,
        'canonical': 3,
        'schema': 4,
        'keywords': 12,
        'keyword_distribution': 8,
        'paragraph_length': 6,
        'links': 3,
        'content_length': 8,
        'core_vitals': 15,
        'eeat': 10,
        'technical_seo': 6,
        'content_freshness': 3,
        'mobile_friendly': 2,
        'https': 3
    }

    class Meta:
        verbose_name = "SEO Analysis"
        verbose_name_plural = "SEO Analyses"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.url} ({self.seo_health_percentage}%)"

    def clean(self):
        super().clean()
        
        # Validate URL format
        if self.url and not self.url.startswith(('http://', 'https://')):
            raise ValidationError({'url': 'URL must start with http:// or https://'})
        
        # Validate keyword density
        if self.keyword_density > 10:
            raise ValidationError({'keyword_density': 'Keyword density seems unusually high'})
        
        # Validate Core Web Vitals ranges
        if self.largest_contentful_paint and self.largest_contentful_paint < 0:
            raise ValidationError({'largest_contentful_paint': 'LCP cannot be negative'})
        
        if self.cumulative_layout_shift and (self.cumulative_layout_shift < 0 or self.cumulative_layout_shift > 1):
            raise ValidationError({'cumulative_layout_shift': 'CLS should be between 0 and 1'})

    def calculate_keyword_stats(self):
        if not self.keyword or self.word_count == 0:
            self.keyword_density = 0.0
            self.recommended_keyword_count = 0
            return
        
        # Calculate current density
        self.keyword_density = round((self.keyword_count / self.word_count) * 100, 2)
        
        # Improved recommended keyword count calculation
        if self.word_count <= 300:
            self.recommended_keyword_count = 1
        elif self.word_count <= 800:
            self.recommended_keyword_count = max(2, round(self.word_count / 250))
        else:
            self.recommended_keyword_count = max(3, round(self.word_count / 300))

    def analyze_headers_structure(self):
        issues = []
        
        # Check H1 count
        if self.h1_count == 0:
            issues.append({
                'type': 'headers',
                'priority': 'critical',
                'message': 'Missing H1 tag. Every page should have exactly one H1.'
            })
        elif self.h1_count > 1:
            issues.append({
                'type': 'headers',
                'priority': 'high',
                'message': f'Multiple H1 tags found ({self.h1_count}). Use only one H1 per page.'
            })
        
        # Check H2 structure
        if self.h2_count == 0 and self.word_count > 300:
            issues.append({
                'type': 'headers',
                'priority': 'medium',
                'message': 'No H2 tags found. Use H2 tags to structure your content.'
            })
        
        # Check for identical H1 and H2 texts
        if self.h1_text and self.h2_texts:
            h1_lower = self.h1_text.lower().strip()
            for i, h2_text in enumerate(self.h2_texts):
                if h1_lower == h2_text.lower().strip():
                    issues.append({
                        'type': 'headers',
                        'priority': 'high',
                        'message': f'H1 and H2 #{i+1} have identical text: "{self.h1_text}"'
                    })
        
        # Check for duplicate H2s
        if self.h2_texts and len(self.h2_texts) != len(set(h2.lower() for h2 in self.h2_texts)):
            issues.append({
                'type': 'headers',
                'priority': 'medium',
                'message': 'Duplicate H2 tags found. Each H2 should be unique.'
            })
        
        return issues

    def analyze_paragraphs(self):
        issues = []
        
        if not self.paragraphs:
            return issues
        
        long_paragraphs = 0
        paragraphs_with_keyword = 0
        total_paragraphs = len(self.paragraphs)
        
        for i, paragraph in enumerate(self.paragraphs):
            paragraph_length = paragraph.get('length', 0)
            paragraph_text = paragraph.get('text', '')
            
            # Check paragraph length (increased threshold)
            if paragraph_length > 200:  # Increased from 160
                long_paragraphs += 1
                if paragraph_length > 300:  # Very long paragraphs
                    issues.append({
                        'type': 'paragraph_length',
                        'priority': 'high',
                        'message': f'Paragraph {i+1} is very long ({paragraph_length} chars). '
                                  'Break it into smaller paragraphs for better readability.'
                    })
            
            # Check keyword in paragraph
            if self.keyword and self.keyword.lower() in paragraph_text.lower():
                paragraphs_with_keyword += 1
        
        # Overall paragraph length assessment
        if long_paragraphs > total_paragraphs * 0.5:  # More than 50% are long
            issues.append({
                'type': 'paragraph_length',
                'priority': 'medium',
                'message': f'{long_paragraphs} of {total_paragraphs} paragraphs are long. '
                          'Consider breaking them up for better readability.'
            })
        
        # Check keyword distribution
        if total_paragraphs > 0 and self.keyword:
            keyword_coverage = paragraphs_with_keyword / total_paragraphs
            if keyword_coverage < 0.2:  # Less than 20%
                issues.append({
                    'type': 'keyword_distribution',
                    'priority': 'medium',
                    'message': f'Keyword "{self.keyword}" appears in only {paragraphs_with_keyword} of '
                              f'{total_paragraphs} paragraphs ({keyword_coverage:.1%}). '
                              'Distribute it more naturally throughout the content.'
                })
            elif keyword_coverage > 0.7:  # More than 70%
                issues.append({
                    'type': 'keyword_distribution',
                    'priority': 'high',
                    'message': f'Keyword "{self.keyword}" appears in {paragraphs_with_keyword} of '
                              f'{total_paragraphs} paragraphs ({keyword_coverage:.1%}). '
                              'This may appear as keyword stuffing.'
                })
        
        return issues

    def check_schema_markup(self):
        issues = []
        
        if not self.has_schema_markup:
            issues.append({
                'type': 'schema',
                'priority': 'high',
                'message': 'No schema markup detected. Implement structured data to improve search visibility.'
            })
            return issues
        
        if not self.schema_types:
            issues.append({
                'type': 'schema',
                'priority': 'medium',
                'message': 'Schema markup detected but type could not be determined.'
            })
            return issues
        
        # Check for schema errors
        if self.schema_errors:
            issues.append({
                'type': 'schema',
                'priority': 'high',
                'message': f'Schema markup has {len(self.schema_errors)} errors. Fix these for proper implementation.'
            })
        
        # Suggest additional schema types based on content
        content_based_suggestions = []
        if self.word_count > 500 and 'Article' not in self.schema_types:
            content_based_suggestions.append('Article')
        if not self.breadcrumb_schema_present:
            content_based_suggestions.append('BreadcrumbList')
        
        if content_based_suggestions:
            issues.append({
                'type': 'schema',
                'priority': 'low',
                'message': f'Consider adding these schema types: {", ".join(content_based_suggestions)}'
            })
        
        return issues

    def calculate_seo_health(self):
        score = 0
        
        # Title optimization (8%)
        if self.title:
            if 50 <= self.title_length <= 60:
                score += self.SEO_WEIGHTS['title']
            elif 30 <= self.title_length <= 70:
                score += self.SEO_WEIGHTS['title'] * 0.7
            elif self.title_length > 0:
                score += self.SEO_WEIGHTS['title'] * 0.3
        
        # Meta description (4%)
        if self.meta_description:
            if 150 <= self.meta_description_length <= 160:
                score += self.SEO_WEIGHTS['meta_description']
            elif 120 <= self.meta_description_length <= 170:
                score += self.SEO_WEIGHTS['meta_description'] * 0.7
        
        # Header structure (11% total)
        if self.h1_count == 1:
            score += self.SEO_WEIGHTS['h1']
        
        if self.h2_count >= 2:
            score += self.SEO_WEIGHTS['headers_structure'] * 0.7
        if self.h3_count >= 1:
            score += self.SEO_WEIGHTS['headers_structure'] * 0.3
        
        # Unique headers check
        headers_unique = True
        if self.h1_text and self.h2_texts:
            h1_lower = self.h1_text.lower().strip()
            if any(h1_lower == h2.lower().strip() for h2 in self.h2_texts):
                headers_unique = False
        
        if headers_unique:
            score += self.SEO_WEIGHTS['headers_unique']
        
        # Images (4%)
        if self.images_count > 0:
            alt_ratio = 1 - (self.missing_alt_images_count / self.images_count)
            score += self.SEO_WEIGHTS['images'] * alt_ratio
        
        # Keywords (20% total)
        if self.keyword and self.keyword_count > 0:
            # Keyword density scoring
            if 1.0 <= self.keyword_density <= 2.5:
                score += self.SEO_WEIGHTS['keywords']
            elif 0.5 <= self.keyword_density <= 3.5:
                score += self.SEO_WEIGHTS['keywords'] * 0.7
            elif self.keyword_density > 0:
                score += self.SEO_WEIGHTS['keywords'] * 0.3
            
            # Keyword distribution
            if self.paragraphs:
                keyword_paragraphs = sum(1 for p in self.paragraphs 
                                       if self.keyword.lower() in p.get('text', '').lower())
                coverage = keyword_paragraphs / len(self.paragraphs)
                if 0.2 <= coverage <= 0.7:
                    score += self.SEO_WEIGHTS['keyword_distribution']
                elif coverage > 0:
                    score += self.SEO_WEIGHTS['keyword_distribution'] * 0.5
        
        # Content quality (14% total)
        # Paragraph length
        if self.paragraphs:
            long_paragraphs = sum(1 for p in self.paragraphs if p.get('length', 0) > 200)
            good_paragraphs_ratio = 1 - (long_paragraphs / len(self.paragraphs))
            score += self.SEO_WEIGHTS['paragraph_length'] * good_paragraphs_ratio
        
        # Content length
        if self.word_count >= 500:
            score += self.SEO_WEIGHTS['content_length']
        elif self.word_count >= 300:
            score += self.SEO_WEIGHTS['content_length'] * 0.7
        elif self.word_count >= 150:
            score += self.SEO_WEIGHTS['content_length'] * 0.3
        
        # Technical SEO (16% total)
        score += self.SEO_WEIGHTS['canonical'] if self.has_canonical else 0
        score += self.SEO_WEIGHTS['schema'] if self.has_schema_markup else 0
        score += self.SEO_WEIGHTS['https'] if self.https else 0
        score += self.SEO_WEIGHTS['mobile_friendly'] if self.mobile_friendly else 0
        
        # Links (3%)
        if self.internal_links_count > 0 and self.external_links_count > 0:
            score += self.SEO_WEIGHTS['links']
        elif self.internal_links_count > 0 or self.external_links_count > 0:
            score += self.SEO_WEIGHTS['links'] * 0.5
        
        # Core Web Vitals (15%)
        cwv_score = self.calculate_core_web_vitals_score()
        score += (cwv_score / 100) * self.SEO_WEIGHTS['core_vitals']
        
        # E-E-A-T (10%)
        eeat_score = self.calculate_eeat_score()
        score += (eeat_score / 100) * self.SEO_WEIGHTS['eeat']
        
        # Technical SEO additional (6%)
        tech_factors = 0
        if self.robots_txt_status:
            tech_factors += 1
        if self.sitemap_status:
            tech_factors += 1
        if self.page_load_time and self.page_load_time <= 3.0:
            tech_factors += 1
        
        score += (tech_factors / 3) * self.SEO_WEIGHTS['technical_seo']
        
        # Content freshness (3%)
        if self.content_freshness:
            days_old = (date.today() - self.content_freshness).days
            if days_old <= 30:
                score += self.SEO_WEIGHTS['content_freshness']
            elif days_old <= 180:
                score += self.SEO_WEIGHTS['content_freshness'] * 0.7
            elif days_old <= 365:
                score += self.SEO_WEIGHTS['content_freshness'] * 0.3
        
        self.seo_health_percentage = min(100, max(0, int(score)))

    def calculate_core_web_vitals_score(self):
        score = 0
        
        # LCP scoring (35% of CWV score)
        if self.largest_contentful_paint is not None:
            if self.largest_contentful_paint <= 2500:
                score += 35
            elif self.largest_contentful_paint <= 4000:
                score += 20
            else:
                score += 5
        
        # FID scoring (25% of CWV score)
        if self.first_input_delay is not None:
            if self.first_input_delay <= 100:
                score += 25
            elif self.first_input_delay <= 300:
                score += 15
            else:
                score += 5
        
        # CLS scoring (40% of CWV score)
        if self.cumulative_layout_shift is not None:
            if self.cumulative_layout_shift <= 0.1:
                score += 40
            elif self.cumulative_layout_shift <= 0.25:
                score += 25
            else:
                score += 10
        
        return score

    def calculate_eeat_score(self):
        score = 0
        
        if self.author_credentials:
            score += 25
        if self.author_bylines:
            score += 20
        if self.citation_sources > 0:
            score += min(25, self.citation_sources * 5)  # Up to 25 points
        if self.contact_info_present:
            score += 15
        
        # Content freshness factor
        if self.last_updated:
            days_old = (datetime.now() - self.last_updated).days
            if days_old <= 90:
                score += 15
            elif days_old <= 365:
                score += 10
            elif days_old <= 730:
                score += 5
        
        return min(100, score)

    def analyze_content_quality(self):
        issues = []
        
        # Word count analysis
        if self.word_count < 300:
            issues.append("Content is too thin ({} words). Aim for at least 300 words.".format(self.word_count))
        elif self.word_count < 500:
            issues.append("Content could be more comprehensive ({} words). Consider expanding to 500+ words.".format(self.word_count))
        
        # Duplicate content
        if self.duplicate_content:
            issues.append("Duplicate content detected. Ensure content is original and unique.")
        
        # Readability
        if self.content_readability_score is not None:
            if self.content_readability_score < 30:
                issues.append("Content is very difficult to read (score: {}). Simplify language and sentence structure.".format(self.content_readability_score))
            elif self.content_readability_score < 50:
                issues.append("Content may be difficult to read (score: {}). Consider simplifying.".format(self.content_readability_score))
        
        # Thin content flag
        if self.thin_content:
            issues.append("Content flagged as thin. Add more valuable, in-depth information.")
        
        return issues

    def generate_recommendations(self):
        self.recommendations = []
        
        # Basic SEO elements
        if not self.title or self.title_length == 0:
            self.recommendations.append({
                'type': 'title',
                'priority': 'critical',
                'message': 'Missing page title. Add a descriptive, keyword-rich title.'
            })
        elif self.title_length < 30:
            self.recommendations.append({
                'type': 'title',
                'priority': 'high',
                'message': f'Title is too short ({self.title_length} chars). Aim for 50-60 characters.'
            })
        elif self.title_length > 70:
            self.recommendations.append({
                'type': 'title',
                'priority': 'high',
                'message': f'Title is too long ({self.title_length} chars). Keep it under 60 characters.'
            })
        
        if not self.meta_description or self.meta_description_length == 0:
            self.recommendations.append({
                'type': 'meta_description',
                'priority': 'high',
                'message': 'Missing meta description. Add a compelling 150-160 character description.'
            })
        elif self.meta_description_length < 120:
            self.recommendations.append({
                'type': 'meta_description',
                'priority': 'medium',
                'message': f'Meta description is short ({self.meta_description_length} chars). Expand to 150-160 characters.'
            })
        
        # Security
        if not self.https:
            self.recommendations.append({
                'type': 'security',
                'priority': 'critical',
                'message': 'Website is not using HTTPS. Migrate to HTTPS for security and SEO benefits.'
            })
        
        # Add all analysis results
        self.recommendations.extend(self.analyze_headers_structure())
        self.recommendations.extend(self.analyze_paragraphs())
        self.recommendations.extend(self.check_schema_markup())
        
        # Content quality issues
        for issue in self.analyze_content_quality():
            self.recommendations.append({
                'type': 'content_quality',
                'priority': 'high',
                'message': issue
            })
        
        # Keyword analysis
        if self.keyword:
            if self.keyword_count == 0:
                self.recommendations.append({
                    'type': 'keyword',
                    'priority': 'critical',
                    'message': f'Target keyword "{self.keyword}" not found in content.'
                })
            elif self.keyword_count < self.recommended_keyword_count:
                self.recommendations.append({
                    'type': 'keyword',
                    'priority': 'medium',
                    'message': f'Keyword "{self.keyword}" appears {self.keyword_count} times. '
                             f'Consider using it {self.recommended_keyword_count} times naturally.'
                })
            
            if self.keyword_density < 0.5:
                self.recommendations.append({
                    'type': 'keyword',
                    'priority': 'medium',
                    'message': f'Keyword density very low ({self.keyword_density:.1f}%). Increase naturally to 1-2%.'
                })
            elif self.keyword_density > 3.0:
                self.recommendations.append({
                    'type': 'keyword',
                    'priority': 'high',
                    'message': f'Keyword density too high ({self.keyword_density:.1f}%). Risk of keyword stuffing.'
                })
        
        # Technical recommendations
        if not self.has_canonical:
            self.recommendations.append({
                'type': 'technical',
                'priority': 'medium',
                'message': 'Add canonical URL to prevent duplicate content issues.'
            })
        
        if not self.mobile_friendly:
            self.recommendations.append({
                'type': 'technical',
                'priority': 'high',
                'message': 'Page is not mobile-friendly. Implement responsive design.'
            })
        
        # Core Web Vitals
        if self.largest_contentful_paint and self.largest_contentful_paint > 2500:
            self.recommendations.append({
                'type': 'performance',
                'priority': 'high',
                'message': f'LCP is slow ({self.largest_contentful_paint}ms). Optimize images and server response time.'
            })
        
        if self.cumulative_layout_shift and self.cumulative_layout_shift > 0.1:
            self.recommendations.append({
                'type': 'performance',
                'priority': 'medium',
                'message': f'CLS is high ({self.cumulative_layout_shift}). Fix layout shifts.'
            })
        
        # Sort recommendations by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        self.recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))

    def has_critical_errors(self):
        critical_conditions = [
            not self.https,
            not self.title or self.title_length == 0,
            self.h1_count == 0,
            self.keyword and self.keyword_count == 0,
            any(rec.get('priority') == 'critical' for rec in self.recommendations)
        ]
        return any(critical_conditions)

    def get_priority_recommendations(self, priority: str) -> List[Dict[str, Any]]:
        return [rec for rec in self.recommendations if rec.get('priority') == priority]

    def get_seo_grade(self) -> str:
        if self.seo_health_percentage >= 90:
            return 'A+'
        elif self.seo_health_percentage >= 80:
            return 'A'
        elif self.seo_health_percentage >= 70:
            return 'B'
        elif self.seo_health_percentage >= 60:
            return 'C'
        elif self.seo_health_percentage >= 50:
            return 'D'
        else:
            return 'F'

    def save(self, *args, **kwargs):
        try:
            # Update basic lengths
            self.title_length = len(self.title.strip()) if self.title else 0
            self.meta_description_length = len(self.meta_description.strip()) if self.meta_description else 0
            
            # Calculate keyword statistics
            self.calculate_keyword_stats()
            
            # Generate recommendations first (needed for scoring)
            self.generate_recommendations()
            
            # Calculate SEO health score
            self.calculate_seo_health()
            
            # Set thin content flag
            self.thin_content = self.word_count < 300
            
        except Exception as e:
            # Log the error in production
            print(f"Error in SEO analysis calculation: {e}")
            # Set default values to prevent save failure
            self.seo_health_percentage = 0
            self.recommendations = [{'type': 'error', 'priority': 'critical', 'message': 'Error in analysis calculation'}]
        
        super().save(*args, **kwargs)