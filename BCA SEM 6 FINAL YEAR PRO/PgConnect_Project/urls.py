"""
URL configuration for PgConnect_Project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from PgConnect_App import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index),
    path('sign_in',views.sign_in,),
    path('sign_up',views.sign_up),
    path('logout',views.logout),
    path('dashboard',views.dashboard),
    path('about_us',views.about_us),
    path('dashboard_add_property',views.dashboard_add_property),
    path('fetchregisterdata',views.fetchregisterdata),
    path('fetchlogindata',views.fetchlogindata),
    path('insertpgdata',views.insertpgdata),
    path('dashboard_property',views.dashboard_property, name='dashboard_property'),
    path('property_details/<int:pg_id>',views.property_details, name='property_details'),
    path('success', views.success, name='payment_status'),
    path('subscriptionplan',views.subscriptionplan, name='subscriptionplan'),
    path('profile',views.profile),
    path('properties',views.properties),
    path('dashboard_edit_property',views.dashboard_edit_property, name='dashboard_edit_property'),
    path('update_pg',views.update_pg, name='update_pg'),
    path('contactus',views.contactus , name='contactus'),
    path("update_profile", views.update_profile),
    path("update_password", views.update_password),
    path('create_order/<int:plan_id>', views.create_order, name='create_order'),
    path('payment_success', views.payment_success, name='payment_success'),
    path('orders', views.orders, name='orders'),
    path('storefeedback', views.storefeedback, name='storefeedback'),
    path('search_pg_view', views.search_pg_view, name='search_pg_view'),
    path('submit-review/<int:id>/', views.submit_review, name='submit_review'),
]+ static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
