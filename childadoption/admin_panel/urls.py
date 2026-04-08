from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.user_list, name='user_list'),
    path('users/view/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/edit/<int:user_id>/', views.user_edit, name='user_edit'),
    path('users/delete/<int:user_id>/', views.user_delete, name='user_delete'),
    path('organizations/', views.organization_list, name='organization_list'),
    path('organization-requests/', views.organization_request_list, name='organization_request_list'),
    path('organization-requests/<int:org_id>/<str:status>/', views.update_organization_status, name='update_organization_status'),
    path('organizations/view/<int:org_id>/', views.organization_detail, name='organization_detail'),
    path('organizations/edit/<int:org_id>/', views.organization_edit, name='organization_edit'),
    path('organizations/delete/<int:org_id>/', views.organization_delete, name='organization_delete'),
    path('children/', views.child_list, name='child_list'),
    path('children/view/<int:child_id>/', views.child_detail, name='child_detail'),
    path('children/edit/<int:child_id>/', views.child_edit, name='child_edit'),
    path('children/delete/<int:child_id>/', views.child_delete, name='child_delete'),
    path('adoption-requests/', views.adoption_request_list, name='adoption_request_list'),
    path('adoption-requests/update/<int:request_id>/', views.update_request_status, name='update_request_status'),
    path('donations/', views.donation_list, name='donation_list'),
    path('sponsorships/', views.sponsorship_list, name='sponsorship_list'),
]
