import logging
import os
import razorpay
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
import requests
from .models import ContactMessage, DonationPayment, Project
from .models import BloodDonor

logger = logging.getLogger(__name__)

# Initialize Razorpay Client
razorpay_client = razorpay.Client(
    auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET)
)


def home(request):
  projects = Project.objects.all().order_by('order', '-date_posted')
  return render(request, 'portfolio/home.html', {'projects': projects})


def portfolio(request):
  projects = Project.objects.all().order_by('order', '-date_posted')
  return render(request, 'portfolio/portfolio.html', {'projects': projects})


def about(request):
  return render(request, 'portfolio/about.html')


def donate(request):
  if request.method == 'POST':
    name = request.POST.get('name')
    email = request.POST.get('email')
    amount = int(request.POST.get('amount'))  # Amount in Rupees

    amount_in_paise = amount * 100  # Convert to paise for Razorpay API

    # Create Razorpay Order
    razorpay_order = razorpay_client.order.create(
        {'amount': amount_in_paise, 'currency': 'INR', 'payment_capture': '1'}
    )

    # Save pending payment to DB
    donation = DonationPayment.objects.create(
        name=name,
        email=email,
        amount=amount,
        razorpay_order_id=razorpay_order['id'],
        status='Pending',
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
  if request.method == 'POST':
    payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_order_id = request.POST.get('razorpay_order_id', '')
    signature = request.POST.get('razorpay_signature', '')

    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': payment_id,
        'razorpay_signature': signature,
    }

    try:
      # Verify payment signature
      razorpay_client.utility.verify_payment_signature(params_dict)

      # Update DB status
      donation = DonationPayment.objects.get(
          razorpay_order_id=razorpay_order_id
      )
      donation.razorpay_payment_id = payment_id
      donation.razorpay_signature = signature
      donation.status = 'Success'
      donation.save()

      # --- SEND AUTOMATED THANK-YOU EMAIL VIA BREVO REST API ---
      brevo_api_key = os.getenv('BREVO_API_KEY') or os.getenv(
          'EMAIL_HOST_PASSWORD'
      )
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
            'to': [{'email': donation.email, 'name': donation.name}],
            (
                'subject'
            ): 'Thank You for Your Generous Donation! ❤️ - Boys Foundation',
            'htmlContent': f"""
                        <div style="font-family: Arial, sans-serif; padding: 20px; color: #333; max-width: 600px; margin: auto; border: 1px solid #e2e8f0; border-radius: 8px;">
                            <h2 style="color: #1a365d;">Thank You, {donation.name}! 🙏</h2>
                            <p>We are deeply grateful for your generous donation of <strong>₹{donation.amount}</strong> to the Boys Foundation.</p>
                            <p>Your support helps us continue our mission and make a meaningful impact in our community.</p>
                            <hr style="border: none; border-top: 1px solid #edf2f7; margin: 20px 0;">
                            <p style="font-size: 0.9em; color: #4a5568;">
                                <strong>Payment ID:</strong> {payment_id}<br>
                                <strong>Order ID:</strong> {razorpay_order_id}<br>
                                <strong>Date:</strong> {donation.created_at.strftime('%B %d, %Y')}
                            </p>
                            <p style="margin-top: 30px; color: #2d3748;">With heartfelt gratitude,<br><strong>Boys Foundation Team</strong></p>
                        </div>
                    """,
        }

        try:
          res = requests.post(url, json=payload, headers=headers, timeout=10)
          print(
              f'Brevo Donation Email Status: {res.status_code}, Response:'
              f' {res.text}'
          )
        except Exception as api_err:
          print(f'BREVO DONATION EMAIL CRASH ERROR: {api_err}')
          logger.error(f'BREVO DONATION EMAIL CRASH ERROR: {api_err}')
      else:
        print('CRITICAL WARNING: BREVO_API_KEY/EMAIL_HOST_PASSWORD not set!')

      messages.success(
          request,
          f'Thank you, {donation.name}! Your donation of ₹{donation.amount} was'
          ' received successfully.',
      )
      return redirect('/donate/')

    except razorpay.errors.SignatureVerificationError:
      DonationPayment.objects.filter(
          razorpay_order_id=razorpay_order_id
      ).update(status='Failed')
      messages.error(request, 'Payment verification failed. Please try again.')
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
    brevo_api_key = os.getenv('BREVO_API_KEY') or os.getenv(
        'EMAIL_HOST_PASSWORD'
    )
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

def project_list(request):
    projects = Project.objects.all().order_by('order', '-date_posted')
    return render(request, 'portfolio/portfolio.html', {'projects': projects})

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'portfolio/project_detail.html', {'project': project})


def blood_support(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        blood_group = request.POST.get('blood_group')
        location = request.POST.get('location', 'Kovur')

        if name and phone and blood_group:
            BloodDonor.objects.create(
                name=name,
                phone=phone,
                blood_group=blood_group,
                location=location
            )
            messages.success(request, "Thank you for registering as a voluntary blood donor! Your support saves lives.")
            return redirect('blood_support')
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'portfolio/blood_support.html')