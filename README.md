# 🔍 SEOAnalysis – Smart SEO Auditing for Django

Welcome to **SEOAnalysis**, a powerful and comprehensive Django model designed to perform deep SEO audits on webpages. Whether you're building a crawler, an SEO tool, or a CMS integration, this model gives you everything you need to evaluate **on-page SEO**, **technical health**, **content quality**, and **E-E-A-T factors** in one elegant structure.

---

## 🚀 Features

### Content Analysis
- Word count, keyword usage, density, paragraph quality  
- Keyword distribution logic and recommendations

### Meta & Header Inspection
- Title and meta description length  
- H1-H2-H3 structure and uniqueness checks

### Technical SEO Signals
- Canonical tag, schema markup types, robots.txt and sitemap presence  
- Render-blocking resources and lazy loading support

### Media Optimization
- Image count, missing alt attributes, compression score

### Core Web Vitals
- LCP, FID, CLS, mobile-friendliness, HTTPS checks

### Content Quality & E-E-A-T
- Readability score, duplicate/thin content, author credentials, update freshness

### Schema & Structured Data Analysis
- Schema type validation, FAQ and breadcrumb detection, rich snippet opportunities

### Actionable Recommendations
- Automatically generated prioritized tips for improving SEO

### SEO Health Score
- Weighted scoring system providing a quick health percentage

---

## 🧠 Built-in Intelligence

Each time a **SEOAnalysis** instance is saved, the model:  
- Calculates SEO scores and health %  
- Generates intelligent recommendations  
- Audits paragraph lengths, keyword spread, and schema quality  
- Flags missing E-E-A-T signals and outdated content  

---

## 🛠️ Usage

Simply integrate this model into your Django project, and populate it with crawled or API-fetched SEO data.

```python

analysis = SEOAnalysis(
    url="https://example.com/page",
    title="Best Coffee in Berlin",
    meta_description="Discover the best coffee spots in Berlin in 2025.",
    word_count=875,
    keyword="coffee berlin",
    keyword_count=10,
    h1_text="Best Coffee in Berlin",
    h2_texts=["Best Coffee in Berlin", "Top Coffee Places"],
    paragraphs=[
        {"length": 120, "text": "Berlin has an amazing coffee culture..."},
        {"length": 200, "text": "Looking for the best coffee in Berlin?"}
    ],
    images_count=5,
    missing_alt_images_count=0,
    has_schema_markup=True,
    schema_types=["Article"],
    has_canonical=True,
    https=True,
    largest_contentful_paint=2100,
    first_input_delay=80,
    cumulative_layout_shift=0.05,
    author_credentials=True,
    contact_info_present=True,
    last_updated=datetime.now()
)
analysis.save()

```

## 📊 Output Example
- **seo_health_percentage:** 88  
- **recommendations:** A list of prioritized SEO improvement tips  
- **has_critical_errors():** Easy boolean check for production monitoring  

---

## 🔒 Security & Performance
- Uses Django's native validators  
- JSONField-based flexibility for paragraphs, schemas, and recommendations  
- Easily extendable for multilingual or domain-specific SEO audits  

---

## 🌐 Perfect For
- SEO tools and dashboards  
- Content and editorial platforms  
- Digital marketing agencies  
- Website health monitoring systems  

---

## ❤️ Why You'll Love It
SEOAnalysis is more than a model—it's an expert SEO assistant built right into your Django app. With smart defaults, actionable feedback, and clean integration, it's your all-in-one solution for SEO intelligence at scale.

---

## 📁 License
MIT – Free for personal and commercial use.

---

## 🤝 Contribute
Pull requests are welcome! If you have suggestions for improvement or want to add new analysis methods, feel free to open an issue or fork the project.