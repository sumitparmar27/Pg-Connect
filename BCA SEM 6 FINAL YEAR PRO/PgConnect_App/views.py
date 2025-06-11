from django.shortcuts import render
from django.shortcuts import redirect,get_object_or_404
from .models import *
from django.contrib import messages
from django.core.paginator import Paginator
from .mailTask import *


def index(request):
    property = add_pg.objects.all()
    pgtypes = pg_type.objects.all()
    locations = add_pg.objects.values_list('area', flat=True)

    context = {
        'property_data': property,
        'pgtypes': pgtypes,
        'locations': locations,
    }
    return render(request, "index.html", context)


def about_us(request):
    return render(request,"about_us.html")

def sign_up(request):
    return render(request,"sign_up.html")

def sign_in(request):
    return render(request,"sign_in.html")

def subscriptionplan(request):
    user_id = request.session['log_id']
    user = register_model.objects.get(id=user_id)

    # Fetch all plans for display
    plans = SubscriptionPlan.objects.all()

    # Fetch all active and expired plans
    active_plan_orders = PlanOrder.objects.filter(
        user=user,
        status='Paid',
        expiration_date__gt=timezone.now()  # Active plans
    )
    expired_plan_orders = PlanOrder.objects.filter(
        user=user,
        status='Paid',
        expiration_date__lte=timezone.now()  # Expired plans
    )

    # Update each plan with additional metadata
    for plan in plans:
        # Check if the plan is the free trial
        plan.is_free_trial = plan.plan_name == "Basic" and plan.price == 0

        # Determine if the plan is active or expired
        if plan.id in active_plan_orders.values_list('plan_id', flat=True):
            plan.status = "Active"
        elif plan.id in expired_plan_orders.values_list('plan_id', flat=True):
            plan.status = "Expired"
        else:
            plan.status = None  # Neither active nor expired

    context = {
        'plans': plans,
    }

    return render(request,"dashboard_pricing.html",context)

from django.utils import timezone
import razorpay

def create_order(request, plan_id):
    uid = request.session['log_id']
    plan = SubscriptionPlan.objects.get(id=plan_id)

    # Check if user already has an active plan
    active_order = PlanOrder.objects.filter(user_id=uid, status='Paid') \
                                    .filter(expiration_date__gt=timezone.now()).first()

    if active_order:
        messages.error(request, "You already have an active plan. You cannot purchase another one.")
        return redirect('subscriptionplan')

    # Handle free trial
    if plan.price == 0:
        # Check if already availed
        free_trial_order = PlanOrder.objects.filter(
            user_id=uid,
            plan=plan
        ).exclude(expiration_date__gt=timezone.now()).first()

        if free_trial_order:
            messages.error(request, "Your free trial has expired. Please purchase another plan.")
            return redirect('subscriptionplan')

        expiration_date = timezone.now() + timezone.timedelta(days=plan.plan_duration)
        PlanOrder.objects.create(
            plan=plan,
            user=register_model(id=uid),
            razorpay_order_id="free_trial",
            amount=0,
            status="Paid",
            expiration_date=expiration_date
        )

        # ✅ Prepare email session data
        request.session['mail_subject'] = "Subscription Activated - Free Trial"
        request.session['mail_message'] = (
            f"Hi {request.user.first_name}, your free trial for the plan "
            f"'{plan.plan_name}' has been activated and will expire on {expiration_date.strftime('%Y-%m-%d')}."
        )

        return redirect('mailtask')

    # Handle paid plan
    try:
        razorpay_client = razorpay.Client(auth=('rzp_test_VQhEfe2NCXbbwI', '2ibreCYL78DA3kjOhobCvz0f'))

        razorpay_order = razorpay_client.order.create({
            "amount": int(plan.price * 100),
            "currency": "INR",
            "payment_capture": '1',
            "receipt": f"order_{uid}",
        })

        expiration_date = timezone.now() + timezone.timedelta(days=plan.plan_duration)
        PlanOrder.objects.create(
            plan=plan,
            user=register_model(id=uid),
            razorpay_order_id=razorpay_order['id'],
            amount=plan.price,
            expiration_date=expiration_date,
            status="Pending"
        )

        context = {
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': 'rzp_test_VQhEfe2NCXbbwI',
            'amount': plan.price,
            'currency': 'INR',
            'plan': plan,
        }
        return render(request, 'payment_page.html', context)

    except razorpay.errors.RazorpayError as e:
        messages.error(request, f"An error occurred while creating the payment order: {e}")
        return redirect('pricing')

    messages.error(request, "An unexpected error occurred. Please try again.")
    return redirect('pricing')
from django.core.mail import send_mail
from django.shortcuts import render, redirect
import razorpay

def payment_success(request):
    if request.method == 'POST':
        # Extract the Razorpay response details from the POST request
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_signature = request.POST.get('razorpay_signature', '')

        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            # Handle missing information
            return render(request, 'failure.html', {'status': 'Error: Missing payment details'})

        # Verify the payment signature with Razorpay
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        }

        try:
            client = razorpay.Client(auth=('rzp_test_VQhEfe2NCXbbwI', '2ibreCYL78DA3kjOhobCvz0f'))
            client.utility.verify_payment_signature(params_dict)

            # Fetch the PlanOrder and update its status
            plan_order = PlanOrder.objects.get(razorpay_order_id=razorpay_order_id)
            plan_order.razorpay_payment_id = razorpay_payment_id
            plan_order.razorpay_signature = razorpay_signature
            plan_order.status = 'Paid'
            plan_order.save()

            subject = 'Payment Successful'
            message = f"Dear {plan_order.user.name},\n\n" \
                      f"Thank you for purchasing the {plan_order.plan.plan_name} plan. Your payment was successful! \n\n" \
                      f"Best regards,\nYour Team"
            sender_email = 'dpoza8125@gmail.com'  # Replace with your sender email address
            recipient_email = [plan_order.user.email]

            send_mail(subject, message, sender_email, recipient_email, fail_silently=False)
            context = {'status': True}
            # Payment was successful
            return render(request, 'success.html', context)

        except razorpay.errors.SignatureVerificationError:
            # Handle invalid signature
            return render(request, 'failure.html', {'status': 'Signature verification failed.'})

        except PlanOrder.DoesNotExist:
            # Handle invalid order
            return render(request, 'failure.html', {'status': 'Order does not exist.'})

        except Exception as e:
            # Handle any other errors
            return render(request, 'failure.html', {'status': f"Error: {str(e)}"})


def contactus(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if Contact.objects.filter(email=email).exists():
            messages.error(request, 'You have already filled contact details.')
            return redirect('/contactus')
        else:
            contactdata = Contact(name=name, email=email, phone=subject, message=message)
            contactdata.save()

            try:
                send_contact_us_email(name, email, subject, message)
                messages.success(request, 'Your message has been sent successfully!')
            except Exception as e:
                print("❌ Email Error:", e)
                messages.warning(request, 'Contact saved, but email sending failed.')

            return redirect('/')

    return render(request, "contact.html")
def dashboard(request):
    if "log_id" in request.session:
        owner_id = request.session["log_id"]  # Get the logged-in owner's ID
        pgdata = add_pg.objects.filter(Pg_ownerid_id=owner_id)
        userid = request.session["log_id"]
        fetchdata = register_model.objects.get(id=userid)
        print(fetchdata)
        context = {
            "pgdata": pgdata,
            "data":fetchdata,
        }
        return render(request, "dashboard.html", context)
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/sign_in/")

def profile(request):
    userid = request.session["log_id"]
    fetchdata = register_model.objects.get(id=userid)
    print(id)
    context = {
        "data":fetchdata,
    }
    return render(request,"dashboard_profile.html" ,context)

def update_profile(request):
    userid = request.session.get("log_id")  # Fetch logged-in user ID
    user = register_model.objects.get(id=userid)  # Fetch user data

    if request.method == "POST":
        user.name = request.POST.get("name")
        user.email = request.POST.get("email")
        user.phone = request.POST.get("phone")
        user.address = request.POST.get("address")

        # Handle profile photo update
        if "profile_photo" in request.FILES:
            user.picture = request.FILES["profile_photo"]

        user.save()  # Save updated user details
        messages.success(request, "Profile updated successfully!")
        return redirect("/dashboard_profile")  # Redirect back to profile page

    context = {"user": user}
    return render(request, "dashboard_profile.html", context)

def update_password(request):
    if request.method == "POST":
        userid = request.session.get("log_id")
        user = register_model.objects.get(id=userid)

        current_password = request.POST["current_password"]
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]

        if user.password != current_password:
            messages.error(request, "Current password is incorrect!")
            return redirect("/profile")

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match!")
            return redirect("/profile")

        user.password = new_password  # Ideally, use hashing for security
        user.save()

        messages.success(request, "Password updated successfully!")
        return redirect("/profile")

    return render(request, "dashboard_profile.html")

def dashboard_add_property(request):
    # pgdata = add_pg.objects.all()
    alltypedata =pg_type.objects.all()
    print(alltypedata)
    context ={
        # "pgdata" : pgdata,
        "typedata" : alltypedata
    }

    return render(request,"dashboard_add_property.html",context)

def dashboard_property(request):
    if "log_id" in request.session:
        owner_id = request.session["log_id"]  # Get the logged-in owner's ID
        pgdata = add_pg.objects.filter(Pg_ownerid_id=owner_id)
        context = {
            "pgdata": pgdata,
        }
        return render(request, "dashboard_property.html", context)
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/sign_in/")

def dashboard_edit_property(request):
    uid = request.session['log_id']
    pgdata = add_pg.objects.get(Pg_ownerid=uid)
    facilities_list = [
        "Air Condition", "HouseKeeping", "Balcony", "Bike Parking",
        "Cable TV", "Wi-Fi", "Reservations", "Washroom", "Kitchen"
    ]
    return render(request,'dashboard_edit_property.html',{'pgdata': pgdata,
        'facilities_list': facilities_list})

def update_pg(request):
    uid = request.session['log_id']
    pg = add_pg.objects.filter(Pg_ownerid=uid)
    sharing_options = ["1 sharing", "2 sharing", "3 sharing", "4 sharing"]
    typedata = pg_type.objects.all()
    facilities_list = [
        "Air Condition", "HouseKeeping", "Balcony", "Bike Parking",
        "Cable TV", "Wi-Fi", "Reservations", "Washroom", "Kitchen"
    ]

    if request.method == 'POST':
        pg.name = request.POST.get('name')
        pgtype = request.POST.get('pgtype')
        if pgtype:  # Check if a valid pgtype is selected
            pg.typeid_id = pgtype
        else:
            # Optionally handle error if pgtype is required
            return render(request, 'dashboard_edit_property.html', {
                'pgdata': pg,
                'typedata': typedata,
                'sharing_options': sharing_options,
                'facilities_list': facilities_list,
                'error': 'PG Type is required.'
            })

        pg.sharing = request.POST.get('sharing')
        pg.area = request.POST.get('area')
        pg.landmark = request.POST.get('landmark')
        pg.address = request.POST.get('address')
        pg.pincode = request.POST.get('pincode')
        pg.price = request.POST.get('price')
        pg.status = request.POST.get('status')
        pg.description = request.POST.get('description')
        pg.rooms = request.POST.get('room')
        pg.bed = request.POST.get('bed')
        pg.Bathroom = request.POST.get('bathroom')
        pg.kitchen = request.POST.get('kitchen')
        pg.balcony = request.POST.get('balcony')
        pg.parking = request.POST.get('parking')
        pg.facilities = request.POST.get('selected_services')

        # Images and video
        if request.FILES.get('img1'): pg.img1 = request.FILES['img1']
        if request.FILES.get('img2'): pg.img2 = request.FILES['img2']
        if request.FILES.get('img3'): pg.img3 = request.FILES['img3']
        if request.FILES.get('img4'): pg.img4 = request.FILES['img4']
        if request.FILES.get('video'): pg.video = request.FILES['video']

        pg.save()
        return redirect('dashboard_property')

    return render(request, 'dashboard_edit_property.html', {
        'pgdata': pg,
        'typedata': typedata,
        'sharing_options': sharing_options,
        'facilities_list': facilities_list
    })




import razorpay
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import add_pg, Booking, register_model


def property_details(request, pg_id):
    uid = request.session['log_id']
    # Fetch PG data based on the provided pg_id
    pg_data = add_pg.objects.get(id=pg_id)
    # facilities_list = pg_data.facilities.split(',') if pg_data.facilities else []
    facilities_list = [f.strip() for f in pg_data.facilities.split(',')] if pg_data.facilities else []
    reviews = PropertyReview.objects.filter(property=pg_data).order_by('-created_at')

    # Fetch services related to the PG (e.g., specific services offered by this PG)

    # Default total price, starting with PG rent price
    total_price = pg_data.price

    if request.method == 'POST':
        # Razorpay integration
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
        amount = int(total_price * 100)  # Convert to paisa
        data = {
            "amount": amount,
            "currency": "INR",
            "receipt": f"order_{pg_id}",
            "payment_capture": 1
        }

        try:
            razorpay_payment = client.order.create(data=data)
            razorpay_order_id = razorpay_payment['id']

            # Create a Booking entry
            booking = Booking.objects.create(
                user=register_model(id=uid),
                pg_id=pg_data,
                total_price=total_price,
                razorpay_order_id=razorpay_order_id,
                status='pending',
            )

            # Associate selected services with the booking

            booking.save()  # Save the booking instance after adding services

            # Pass required data to the template for Razorpay payment
            context = {
                'razorpay_payment': {
                    'amount': amount,
                    'order_id': razorpay_order_id,
                    'key': settings.RAZORPAY_KEY_ID,
                },
                'data': pg_data,
                'total_price': total_price,
                'booking': booking,
            }
            return render(request, 'property_details.html', context)

        except razorpay.errors.BadRequestError as e:
            messages.error(request, f'BadRequestError: {str(e)}')
        except razorpay.errors.ServerError as e:
            messages.error(request, f'ServerError: {str(e)}')
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')

        return redirect('property_details', pg_id=pg_id)

    context = {
        'data': pg_data,
        'total_price': total_price,
        'facilities_list': facilities_list,
        'reviews': reviews,
    }

    return render(request, 'property_details.html', context)


def success(request):
    response = request.POST
    params_dict = {
        'razorpay_order_id': response['razorpay_order_id'],
        'razorpay_payment_id': response['razorpay_payment_id'],
        'razorpay_signature': response['razorpay_signature'],
    }

    client = razorpay.Client(
        auth=('rzp_test_VQhEfe2NCXbbwI', '2ibreCYL78DA3kjOhobCvz0f')
    )

    try:
        # Verify the payment signature
        client.utility.verify_payment_signature(params_dict)

        # Get the order based on the Razorpay order ID
        order = Booking.objects.get(razorpay_order_id=response['razorpay_order_id'])

        # Update the Razorpay payment ID and signature in the order
        order.razorpay_payment_id = response['razorpay_payment_id']
        order.razorpay_signature = response['razorpay_signature']

        # Set the status to 'paid' if payment is successful
        order.status = 'paid'
        order.save()

        # Send a confirmation email
        subject = 'Payment Successful'
        message = f"Dear {order.user.name},\n\n" \
                  f"Your payment for Order ID {order.id} has been successfully processed. Thank you for choosing us!\n\n" \
                  f"Best regards,\nYour Team"
        sender_email = 'dpoza8125@gmail.com'  # Replace with your sender email address
        recipient_email = [order.user.email]

        send_mail(subject, message, sender_email, recipient_email, fail_silently=False)

        return render(request, 'booking_success.html', {'status': True})

    except razorpay.errors.SignatureVerificationError:
        # Handle signature verification errors
        print("Signature verification failed.")
        return render(request, 'booking_success.html', {'status': False})

    except Exception as e:
        # Handle other exceptions
        print(f"Error occurred: {str(e)}")
        return render(request, 'booking_success.html', {'status': False})

def orders(request):
    uid = request.session['log_id']
    alldata = Booking.objects.filter(user=uid)
    context = {
        'data':alldata,
    }
    return render(request,'dashboard_order.html',context)

def storefeedback(request):
    uid = request.session.get('log_id')  # Ensure user is logged in and has a session
    user = register_model.objects.get(id=uid)

    # Get all products the user has ordered (assuming an Order or ProductCart model)
    all_products = add_pg.objects.all()
    context = {"orderdetails": all_products}

    if request.method == 'POST':
        order_id = request.POST.get('orders')
        ratings = request.POST.get('ratings')
        feedback_message = request.POST.get('feedback_message')

        if Review.objects.filter(pg_id=order_id).exists():
            messages.error(request, 'you have already filled feedback.')
            return redirect(index)
        else:
        # Assuming 'product' is a ForeignKey in the Feedback model pointing to Product
            review = Review.objects.create(
                user=register_model(id=uid),
                pg_id=add_pg.objects.get(id=order_id),
                ratings=ratings,
                comment=feedback_message,
            )

        messages.success(request, "Review is submitted")
        return redirect(index)
    return render(request, 'dashboard_review.html', context)


def submit_review(request, id):
    if request.method == 'POST':
        property_obj = get_object_or_404(add_pg, id=id)
        PropertyReview.objects.create(
            property=property_obj,
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            message=request.POST.get('message'),
            rating=int(request.POST.get('rating') or 0)
        )
    return redirect('property_details', pg_id=id)

def properties(request):
    property = add_pg.objects.all()
    paginator = Paginator(property, 6)
    page_number = request.GET.get('page')
    property = paginator.get_page(page_number)
    property_data = []
    context = {
            'property_data': property,
    }
    return render(request,"property_grid_view.html",context)




def fetchregisterdata(request):
    name = request.POST.get("name")
    email = request.POST.get("email")
    phone = request.POST.get("phone")
    address = request.POST.get("address")
    password = request.POST.get("password")
    role = request.POST.get("role")

    profile_image = request.FILES["dp_image"]


    insertquery = register_model(name = name,email=email,phone=phone,address=address,password = password ,role = role,picture = profile_image)
    insertquery.save()
    return render(request,"sign_in.html")


def fetchlogindata(request):
    email = request.POST.get("email")
    password = request.POST.get("password")

    print(email)
    print(password)

    try:
        selectquery = register_model.objects.get(email=email,password=password)
        print(selectquery)
        print("success")

        request.session["log_id"] = selectquery.id
        request.session["log_name"] = selectquery.name
        request.session["log_email"] = selectquery.email
        request.session["log_role"] = selectquery.role

        usersessionid = request.session["log_id"]
        print("Session id :", usersessionid)

    except:
        selectquery = None


    if selectquery is not None:
        return redirect(profile)
    else:
        messages.error(request,"Invalid Email or Password")
        return render(request,"sign_in.html")

def insertpgdata(request):
    name = request.POST.get("name")
    typeid = request.POST.get("pgtype")
    sharing = request.POST.get("sharing")
    area = request.POST.get("area")
    landmark = request.POST.get("landmark")
    address = request.POST.get("address")
    pincode  = request.POST.get("pincode")
    price  = request.POST.get("price")
    status = request.POST.get("status")
    description = request.POST.get("description")
    room = request.POST.get("room")
    bed = request.POST.get("bed")
    bathroom = request.POST.get("bathroom")
    kitchen = request.POST.get("kitchen")
    balcony = request.POST.get("balcony")
    parking = request.POST.get("parking")
    img1 = request.FILES.get("img1")
    img2 = request.FILES.get("img2")
    img3 = request.FILES.get("img3")
    img4 = request.FILES.get("img4")
    video = request.FILES.get("video")
    services  = request.POST.get("selected_services")
    ownerid  = request.session["log_id"]

    insertquery = add_pg(name=name,
                typeid=pg_type(id=typeid),
                sharing=sharing,
                area=area,
                landmark=landmark,
                address=address,
                pincode=pincode,
                price=price,
                status=status,
                description=description,
                rooms=room,
                bed=bed,
                Bathroom=bathroom,
                kitchen=kitchen,
                balcony=balcony,
                parking=parking,
                facilities=services,
                img1=img1,
                img2=img2,
                img3=img3,
                img4=img4,
                video=video,
                Pg_ownerid=register_model(id=ownerid),upload_datetime=now() )
    insertquery.save()
    messages.success(request,"PG successfully added")
    return render(request,"dashboard_add_property.html")







def logout(request):
    try:
        del request.session["log_id"]
        del request.session["log_name"]
        del request.session["log_email"]
        del request.session["log_role"]

    except:
        pass

    return redirect("/")


from django.shortcuts import render
from .models import add_pg, pg_type

def search_pg_view(request):
    locations = add_pg.objects.values_list('area', flat=True)

    pgtypes = pg_type.objects.all()

    selected_location = request.GET.get('location')
    selected_pgtype = request.GET.get('pgtype')
    selected_price_range = request.GET.get('price_range')

    print("Selected location:", selected_location)
    print("Selected PG Type:", selected_pgtype)
    print("Selected Price Range:", selected_price_range)

    pgs = add_pg.objects.all()
    if selected_location:
        pgs = pgs.filter(area=selected_location)
    if selected_pgtype:
        pgs = pgs.filter(typeid_id=selected_pgtype)
    if selected_price_range:
        try:
            price_min, price_max = map(int, selected_price_range.split('-'))
            print("Filtering price between:", price_min, "and", price_max)
            pgs = pgs.filter(price__gte=price_min, price__lte=price_max)
        except ValueError:
            print("Price range format error.")

    print("Final Queryset Count:", pgs.count())

    return render(request, 'property_grid_view.html', {
        'property_data': pgs,
        'locations': locations,
        'pgtypes': pgtypes,
        'selected_location': selected_location,
        'selected_pgtype': selected_pgtype,
        'selected_price_range': selected_price_range,
    })
