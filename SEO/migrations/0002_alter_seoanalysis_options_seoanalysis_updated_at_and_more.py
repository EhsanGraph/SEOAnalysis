# Generated by Django 5.2.1 on 2025-05-26 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SEO', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='seoanalysis',
            options={'ordering': ['-created_at'], 'verbose_name': 'SEO Analysis', 'verbose_name_plural': 'SEO Analyses'},
        ),
        migrations.AddField(
            model_name='seoanalysis',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='seoanalysis',
            name='content_freshness',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='seoanalysis',
            name='content_readability_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='seoanalysis',
            name='cumulative_layout_shift',
            field=models.FloatField(blank=True, null=True, verbose_name='CLS'),
        ),
        migrations.AlterField(
            model_name='seoanalysis',
            name='first_input_delay',
            field=models.FloatField(blank=True, null=True, verbose_name='FID (ms)'),
        ),
        migrations.AlterField(
            model_name='seoanalysis',
            name='image_compression_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='seoanalysis',
            name='largest_contentful_paint',
            field=models.FloatField(blank=True, null=True, verbose_name='LCP (ms)'),
        ),
        migrations.AlterField(
            model_name='seoanalysis',
            name='last_updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='seoanalysis',
            name='page_load_time',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
