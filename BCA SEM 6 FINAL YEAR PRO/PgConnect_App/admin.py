from django.contrib import admin
from .models import *


# Register your models here.

class showregister(admin.ModelAdmin):
    list_display = ["id","name","email","phone","address","password","role","user_picture"]

admin.site.register(register_model,showregister)

class showpgtype(admin.ModelAdmin):
    list_display = ["id","name"]

admin.site.register(pg_type,showpgtype)

class showpg(admin.ModelAdmin):
    list_display = ["id","name","typeid","sharing","area","landmark","address","pincode","price","status","description","rooms","bed","Bathroom","kitchen","balcony","parking","pg_img1","pg_img2","pg_img3","pg_img4","video","facilities","Pg_ownerid","upload_datetime"]

admin.site.register(add_pg,showpg)

@admin.register(SubscriptionPlan)
class SubscriptionPlansAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'plan_duration', 'price', 'description', 'discount','renewable','max_properties','is_free_trial','creation_date')

@admin.register(PlanOrder)
class PlanorderAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature','amount','status','purchase_date','expiration_date')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user','pg_id', 'total_price', 'razorpay_order_id', 'razorpay_payment_id','razorpay_signature','status','created_at')

@admin.register(Review)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ('user', 'pg_id', 'ratings', 'comment','comment', 'timestamp')

class reviews(admin.ModelAdmin):
    list_display = ['id','name','email','message','rating','created_at','property']
admin.site.register(PropertyReview,reviews)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'message', 'timestamp')