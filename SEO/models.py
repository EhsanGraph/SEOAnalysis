from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime

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
    largest_contentful_paint = models.FloatField(null=True, verbose_name="LCP (ms)")
    first_input_delay = models.FloatField(null=True, verbose_name="FID (ms)")
    cumulative_layout_shift = models.FloatField(null=True, verbose_name="CLS")
    mobile_friendly = models.BooleanField(default=False)
    https = models.BooleanField(default=False)

    # Content Quality Signals
    content_readability_score = models.FloatField(null=True)  # Flesch-Kincaid
    duplicate_content = models.BooleanField(default=False)
    thin_content = models.BooleanField(default=False)
    content_freshness = models.DateField(null=True)
    semantic_keywords = models.JSONField(default=list)  # LSI keywords

    # Advanced Technical SEO
    robots_txt_status = models.BooleanField(default=False)
    sitemap_status = models.BooleanField(default=False)
    page_load_time = models.FloatField(null=True)  # in seconds
    render_blocking_resources = models.JSONField(default=list)
    lazy_loading_images = models.BooleanField(default=False)

    # Enhanced Schema Markup Analysis
    schema_errors = models.JSONField(default=list)
    rich_snippet_opportunities = models.JSONField(default=list)
    faq_schema_present = models.BooleanField(default=False)
    breadcrumb_schema_present = models.BooleanField(default=False)

    # EEA-T Factors
    author_credentials = models.BooleanField(default=False)
    author_bylines = models.BooleanField(default=False)
    citation_sources = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(null=True)
    contact_info_present = models.BooleanField(default=False)

    # Scoring
    seo_health_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # For multilingual SEO
    hreflang_implemented = models.BooleanField(default=False)

    # For image optimization
    image_compression_score = models.FloatField(null=True)

    # For security
    security_headers = models.JSONField(default=list)

    recommendations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    SEO_WEIGHTS = {
        'title': 10,
        'meta_description': 5,
        'h1': 5,
        'headers_structure': 5,
        'headers_unique': 5,
        'images': 5,
        'canonical': 5,
        'schema': 5,
        'keywords': 15,
        'keyword_distribution': 10,
        'paragraph_length': 10,
        'links': 5,
        'content_length': 10,
        'core_vitals': 20,
        'eeat': 15,
        'technical_seo': 10,
        'content_freshness': 5
    }

    def __str__(self):
        return self.url

    def calculate_keyword_stats(self):
        if not self.keyword or self.word_count == 0:
            self.keyword_density = 0.0
            self.recommended_keyword_count = 0
            return
        
        # Calculate current density
        self.keyword_density = (self.keyword_count / self.word_count) * 100
        
        # Recommended keyword count (1 per 300 words)
        self.recommended_keyword_count = max(1, round(self.word_count / 300))
        
        # Check if H1 and H2 are same
        if self.h1_text and self.h2_texts:
            for h2_text in self.h2_texts:
                if self.h1_text.lower() == h2_text.lower():
                    self.recommendations.append({
                        'type': 'headers',
                        'priority': 'high',
                        'message': f'H1 and H2 have identical text: "{self.h1_text}"'
                    })

    def analyze_paragraphs(self):
        long_paragraphs = 0
        paragraphs_with_keyword = 0
        
        for i, paragraph in enumerate(self.paragraphs):
            # Check paragraph length
            if paragraph.get('length', 0) > 160:
                long_paragraphs += 1
                self.recommendations.append({
                    'type': 'paragraph_length',
                    'priority': 'medium',
                    'message': f'Paragraph {i+1} is too long ({paragraph["length"]} chars). '
                              'Keep paragraphs under 160 characters for readability.'
                })
            
            # Check keyword in paragraph
            if self.keyword and self.keyword.lower() in paragraph.get('text', '').lower():
                paragraphs_with_keyword += 1
        
        # Check keyword distribution
        if self.paragraphs and self.keyword:
            keyword_coverage = paragraphs_with_keyword / len(self.paragraphs)
            if keyword_coverage < 0.3:  # At least 30% of paragraphs should contain keyword
                self.recommendations.append({
                    'type': 'keyword_distribution',
                    'priority': 'medium',
                    'message': f'Keyword "{self.keyword}" appears in only {paragraphs_with_keyword} of '
                              f'{len(self.paragraphs)} paragraphs. Distribute it more evenly.'
                })

    def check_schema_markup(self):
        if not self.has_schema_markup:
            self.recommendations.append({
                'type': 'schema',
                'priority': 'high',
                'message': 'No schema markup detected. Implement structured data.'
            })
        elif not self.schema_types:
            self.recommendations.append({
                'type': 'schema',
                'priority': 'medium',
                'message': 'Schema markup detected but type could not be determined.'
            })
        else:
            # Check for important schema types
            important_schemas = {'Article', 'WebPage', 'LocalBusiness', 'Product'}
            missing_schemas = important_schemas - set(self.schema_types)
            
            if missing_schemas:
                self.recommendations.append({
                    'type': 'schema',
                    'priority': 'low',
                    'message': f'Consider adding these schema types: {", ".join(missing_schemas)}'
                })

    def calculate_seo_health(self):
        score = 0
        
        # Title check (10%)
        if 50 <= self.title_length <= 60:
            score += self.SEO_WEIGHTS['title']
        elif self.title_length > 0:
            score += self.SEO_WEIGHTS['title'] * 0.5

        # Meta Description check (5%)
        if 150 <= self.meta_description_length <= 160:
            score += self.SEO_WEIGHTS['meta_description']

        # Header checks (10%)
        if self.h1_count == 1:
            score += self.SEO_WEIGHTS['h1']
        if self.h2_count >= 2 and self.h3_count >= 3:
            score += self.SEO_WEIGHTS['headers_structure']
        
        # Unique headers check
        if self.h1_text and self.h2_texts:
            all_unique = True
            if self.h1_text.lower() in [h2.lower() for h2 in self.h2_texts]:
                all_unique = False
            if all_unique:
                score += self.SEO_WEIGHTS['headers_unique']

        # Image checks (5%)
        if self.missing_alt_images_count == 0 and self.images_count > 0:
            score += self.SEO_WEIGHTS['images']
        elif self.missing_alt_images_count < self.images_count:
            score += self.SEO_WEIGHTS['images'] * 0.5

        # Keyword checks (25%)
        ideal_density = 1.5  # 1-2% is ideal
        if 1.0 <= self.keyword_density <= 2.5:
            score += self.SEO_WEIGHTS['keywords']
        elif self.keyword_density > 0:
            score += self.SEO_WEIGHTS['keywords'] * 0.5
        
        # Keyword distribution in paragraphs
        if self.paragraphs and self.keyword:
            keyword_paragraphs = sum(1 for p in self.paragraphs if self.keyword.lower() in p.get('text', '').lower())
            coverage = keyword_paragraphs / len(self.paragraphs)
            if coverage >= 0.3:
                score += self.SEO_WEIGHTS['keyword_distribution']

        # Paragraph length checks
        long_paragraphs = sum(1 for p in self.paragraphs if p.get('length', 0) > 160)
        if long_paragraphs == 0 and self.paragraphs:
            score += self.SEO_WEIGHTS['paragraph_length']

        # Content length
        if self.word_count >= 300:
            score += self.SEO_WEIGHTS['content_length']
        elif self.word_count >= 150:
            score += self.SEO_WEIGHTS['content_length'] * 0.5

        # Technical SEO
        score += self.SEO_WEIGHTS['canonical'] if self.has_canonical else 0
        score += self.SEO_WEIGHTS['schema'] if self.has_schema_markup else 0
        
        # Core Web Vitals (20%)
        score += self.calculate_core_web_vitals_score() * 0.2
        
        # E-E-A-T Scoring (15%)
        eeat_factors = self.check_eeat_factors()
        if not eeat_factors:  # No issues found
            score += self.SEO_WEIGHTS['eeat']
        elif len(eeat_factors) < 3:  # Some issues
            score += self.SEO_WEIGHTS['eeat'] * 0.5

        self.seo_health_percentage = min(100, int(score))


    def generate_recommendations(self):
        self.recommendations = []

        # content quality issues
        for issue in self.analyze_content_quality():
            self.recommendations.append({
                'type': 'content_quality',
                'priority': 'high',
                'message': issue
            })
        
        # Keyword recommendations
        if self.keyword:
            if self.keyword_count < self.recommended_keyword_count:
                self.recommendations.append({
                    'type': 'keyword',
                    'priority': 'medium',
                    'message': f'Keyword "{self.keyword}" appears {self.keyword_count} times. '
                             f'Recommended: {self.recommended_keyword_count} times (1 per 300 words).'
                })
            
            if self.keyword_density < 1.0:
                self.recommendations.append({
                    'type': 'keyword',
                    'priority': 'high',
                    'message': f'Keyword density too low ({self.keyword_density:.1f}%). '
                             'Aim for 1-2% density.'
                })
            elif self.keyword_density > 2.5:
                self.recommendations.append({
                    'type': 'keyword',
                    'priority': 'high',
                    'message': f'Keyword density too high ({self.keyword_density:.1f}%). '
                             'Risk of keyword stuffing. Aim for 1-2% density.'
                })

        # Add all other existing recommendations
        self.analyze_paragraphs()
        self.check_schema_markup()
        
        # Sort recommendations by priority (critical, high, medium, low)
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        self.recommendations.sort(key=lambda x: priority_order[x['priority']])


    def calculate_core_web_vitals_score(self):
        score = 0
        # LCP (Should be < 2.5s)
        if self.largest_contentful_paint and self.largest_contentful_paint <= 2500:
            score += 30
        # FID (Should be < 100ms)
        if self.first_input_delay and self.first_input_delay <= 100:
            score += 30
        # CLS (Should be < 0.1)
        if self.cumulative_layout_shift and self.cumulative_layout_shift <= 0.1:
            score += 40
        return score

    def check_eeat_factors(self):
        factors = []
        if not self.author_credentials:
            factors.append("Author credentials missing")
        if not self.last_updated or (datetime.now() - self.last_updated).days > 365:
            factors.append("Content may be outdated")
        if not self.contact_info_present:
            factors.append("Contact information missing")
        return factors

    def analyze_content_quality(self):
        issues = []
        if self.word_count < 500:
            issues.append("Content may be too thin ({} words)".format(self.word_count))
        if self.duplicate_content:
            issues.append("Duplicate content detected")
        if self.content_readability_score and self.content_readability_score < 60:
            issues.append("Content may be difficult to read (score: {})".format(self.content_readability_score))
        return issues


    def has_critical_errors(self):
        return any(
            rec['priority'] == 'critical' 
            for rec in self.recommendations
        ) or not self.https

    def save(self, *args, **kwargs):
        # Update lengths
        self.title_length = len(self.title) if self.title else 0
        self.meta_description_length = len(self.meta_description) if self.meta_description else 0
        
        # Calculate keyword stats
        self.calculate_keyword_stats()
        
        # Generate scores and recommendations
        self.calculate_seo_health()
        self.generate_recommendations()
        
        super().save(*args, **kwargs)