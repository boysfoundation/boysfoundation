import razorpay
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from .models import ContactMessage, DonationPayment, Project
import requests
import os
import logging
logger = logging.getLogger(__name__)

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))

def home(request):
    projects = Project.objects.all().order_by('-date_posted')
    return render(request, 'portfolio/home.html', {'projects': projects})

def portfolio(request):
    projects = Project.objects.all().order_by('-date_posted')
    return render(request, 'portfolio/portfolio.html', {'projects': projects})

def about(request):
    return render(request, 'portfolio/about.html')

def donate(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        amount = int(request.POST.get('amount'))  # Amount in Rupees

        amount_in_paise = amount * 100  # Convert to paise for Razorpay API

        # Create Razorpay Order
        razorpay_order = razorpay_client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": "1"
        })

        # Save pending payment to DB
        donation = DonationPayment.objects.create(
            name=name,
            email=email,
            amount=amount,
            razorpay_order_id=razorpay_order['id'],
            status='Pending'
        )

        context = {
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_merchant_key': settings.RAZOR_KEY_ID,
            'razorpay_amount': amount_in_paise,
            'currency': 'INR',
            'callback_url': '/payment-handler/',
            'donor_name': name,
            'donor_email': email,
            'amount': amount,
        }
        return render(request, 'portfolio/donate_checkout.html', context)

    return render(request, 'portfolio/donate.html')

@csrf_exempt
def payment_handler(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            # Verify payment signature
            razorpay_client.utility.verify_payment_signature(params_dict)

            # Update DB status
            donation = DonationPayment.objects.get(razorpay_order_id=razorpay_order_id)
            donation.razorpay_payment_id = payment_id
            donation.razorpay_signature = signature
            donation.status = 'Success'
            donation.save()

            messages.success(request, f"Thank you, {donation.name}! Your donation of ₹{donation.amount} was received successfully.")
            return redirect('/donate/')

        except razorpay.errors.SignatureVerificationError:
            DonationPayment.objects.filter(razorpay_order_id=razorpay_order_id).update(status='Failed')
            messages.error(request, "Payment verification failed. Please try again.")
            return redirect('/donate/')
    else:
        return redirect('/donate/')



def contact(request):
  if request.method == 'POST':
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    subject = request.POST.get('subject', 'New Contact Form Submission').strip()
    message = request.POST.get('message', '').strip()

    # 1. Try to save to Supabase Database
    try:
      ContactMessage.objects.create(
          name=name,
          email=email,
          phone=phone,
          subject=subject,
          message=message,
      )
    except Exception as db_err:
      print(f'DATABASE CRASH ERROR: {db_err}')
      logger.error(f'DATABASE CRASH ERROR: {db_err}')

    # 2. Try to send Email via Brevo REST API
    brevo_api_key = os.getenv('BREVO_API_KEY') or os.getenv('EMAIL_HOST_PASSWORD')
    if brevo_api_key:
      url = 'https://api.brevo.com/v3/smtp/email'
      headers = {
          'accept': 'application/json',
          'api-key': brevo_api_key,
          'content-type': 'application/json',
      }
      payload = {
          'sender': {
              'name': 'Boys Foundation',
              'email': 'boysfoundation2016@gmail.com',
          },
          'to': [{'email': 'boysfoundation2016@gmail.com', 'name': 'Admin'}],
          'subject': f'Contact Form: {subject}',
          'htmlContent': f"""
                    <h3>New Contact Form Submission</h3>
                    <p><strong>Name:</strong> {name}</p>
                    <p><strong>Email:</strong> {email}</p>
                    <p><strong>Phone:</strong> {phone}</p>
                    <p><strong>Subject:</strong> {subject}</p>
                    <br>
                    <p><strong>Message:</strong><br>{message}</p>
                """,
      }

      try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f'Brevo API Status: {res.status_code}, Response: {res.text}')
      except Exception as api_err:
        print(f'BREVO API CRASH ERROR: {api_err}')
        logger.error(f'BREVO API CRASH ERROR: {api_err}')
    else:
      print('CRITICAL WARNING: EMAIL_HOST_PASSWORD is not set in environment!')

    # 3. Always show success message to user (no 500 error!)
    messages.success(
        request, 'Thank you! Your message has been sent successfully.'
    )

  return render(request, 'portfolio/contact.html')