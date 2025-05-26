from django.urls import path
from . import views

app_name = 'seo_analyzer'

urlpatterns = [
    path('', views.HomeView.as_view(), name='index'),
    path('analyze/', views.AnalyzeURLView.as_view(), name='analyze_url'),
    path('analysis/<int:pk>/', views.AnalysisDetailView.as_view(), name='analysis_detail'),
    path('analyses/', views.AnalysisListView.as_view(), name='analysis_list'),
    path('bulk-analysis/', views.BulkAnalysisView.as_view(), name='bulk_analysis'),
    path('compare/', views.CompareAnalysisView.as_view(), name='compare_analyses'),
    path('delete/<int:pk>/', views.DeleteAnalysisView.as_view(), name='delete_analysis'),
    path('api/analysis/<int:pk>/', views.AnalysisAPIView.as_view(), name='analysis_api'),
]