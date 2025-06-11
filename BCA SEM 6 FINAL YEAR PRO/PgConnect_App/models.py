from tkinter.constants import CASCADE

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils import timezone
from dateutil.relativedelta import relativedelta  # Use this for month-based delta
# Create your models here.

class register_model(models.Model):
    name =models.CharField(max_length=30)
    email = models.EmailField()
    phone = models.BigIntegerField(null=True)
    address = models.TextField(null=True)
    password = models.CharField(max_length=6)
    role = models.CharField(max_length=20)
    picture = models.ImageField(upload_to='photos')

    def user_picture(self):
        return mark_safe('<img src="{}" width="100"/'.format(self.picture.url))

    user_picture.allow_tag = True

    def __str__(self):
        return self.name

class pg_type(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class add_pg(models.Model):
    name = models.CharField(max_length=30)
    typeid = models.ForeignKey(pg_type, on_delete=models.CASCADE)
    sharing = models.CharField(max_length=30,null=True, blank=True)
    area = models.CharField(max_length=30)
    landmark = models.CharField(max_length=30)
    address = models.TextField()
    pincode = models.IntegerField()
    price = models.IntegerField()
    status = models.CharField(max_length=30,null=True, blank=True)
    description = models.TextField()
    rooms = models.IntegerField()
    bed = models.IntegerField()
    Bathroom = models.IntegerField()
    kitchen  = models.IntegerField()
    balcony = models.IntegerField()
    parking = models.IntegerField()
    facilities = models.TextField(blank=True, null=True)  # Store selected facilities
    img1 = models.ImageField(upload_to="photos")
    img2 = models.ImageField(upload_to="photos")
    img3 = models.ImageField(upload_to="photos")
    img4 = models.ImageField(upload_to="photos")
    video = models.FileField(upload_to="videos")
    Pg_ownerid = models.ForeignKey(register_model, on_delete=models.CASCADE, null=True)
    upload_datetime = models.DateTimeField(auto_now_add=True)

    def pg_img1(self):
        return mark_safe(f'<img src="{self.img1.url}" width="100"/>')
    pg_img1.allow_tags = True
    def pg_img2(self):
        return mark_safe('<img src="{}" width="100"/'.format(self.img2.url))
    pg_img2.allow_tags = True
    def pg_img3(self):
        return mark_safe('<img src="{}" width="100"/'.format(self.img3.url))
    pg_img3.allow_tags = True
    def pg_img4(self):
        return mark_safe('<img src="{}" width="100"/'.format(self.img4.url))
    pg_img4.allow_tags = True

    def __str__(self):
        return self.name



class SubscriptionPlan(models.Model):
    plan_name = models.CharField(max_length=255, null=False)  # Name of the subscription
    plan_duration = models.IntegerField(null=False)  # Duration in days or months
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)  # Price of the subscription plan
    description = models.TextField(blank=True, null=True)  # Description of the plan
    discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # Discount percentage, if applicable
    renewable = models.BooleanField(default=True)  # Whether the plan is renewable
    max_properties = models.IntegerField(default=1)  # Max properties allowed to list under this plan
    is_free_trial = models.BooleanField(default=False)  # Add this field
    creation_date = models.DateTimeField(auto_now_add=True)  # Creation date

    def __str__(self):
        return f"{self.plan_name} ({self.plan_duration} days) - ${self.price}"

class PlanOrder(models.Model):
    user = models.ForeignKey(register_model, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Paid', 'Paid'), ('Failed', 'Failed')], default='Pending')
    purchase_date = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    expiration_date = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Ensure purchase_date is set before calculating expiration_date
        if not self.expiration_date and self.purchase_date:
            self.expiration_date = self.purchase_date + relativedelta(months=self.plan.plan_duration)
        super().save(*args, **kwargs)

    def is_active(self):
        # Check if the current date is before the expiration date
        return self.expiration_date and self.expiration_date > timezone.now()

    def has_personal_trainer(self):
        # Check if the associated plan includes a personal trainer
        return self.plan.personal_trainer if hasattr(self.plan, 'personal_trainer') else False

    def __str__(self):
        return f"Order {self.razorpay_order_id} by {self.user}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
        ('paid', 'Paid'),
        ('not paid', 'Not Paid'),
    ]
    user = models.ForeignKey(register_model, on_delete=models.CASCADE)
    pg_id = models.ForeignKey('add_pg', on_delete=models.CASCADE, null=True, blank=True, default='')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.id} by {self.user.name}"

class Review(models.Model):
    user = models.ForeignKey(register_model, on_delete=models.CASCADE)
    pg_id = models.ForeignKey(add_pg, on_delete=models.CASCADE, null=True, blank=True)
    ratings = models.IntegerField()
    comment = models.CharField(max_length=300, default="")
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Feedback from {self.user.name}"

class PropertyReview(models.Model):
    property = models.ForeignKey(add_pg, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    rating = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.property.name}"

class Contact(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=11)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name