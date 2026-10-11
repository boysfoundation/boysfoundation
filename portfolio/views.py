import razorpay
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from .models import ContactMessage, DonationPayment, Project

# Initialize Razorpay Client
razorpay_client = razorpay.Client(
    auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET)
)


def home(request):
  projects = Project.objects.all().order_by('-date_posted')
  return render(request, 'portfolio/home.html', {'projects': projects})


def portfolio(request):
  projects = Project.objects.all().order_by('-date_posted')
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

      # --- OPTION 2: SEND DONATION RECEIPT EMAIL TO DONOR ---
      receipt_subject = (
          'Donation Receipt - Thank you for supporting Boys Foundation'
      )
      receipt_body = (
          f'Dear {donation.name},\n\n'
          f'Thank you for your generous contribution of ₹{donation.amount} to Best One Young Society!\n\n'
          f'Payment Summary:\n'
          f'- Order ID: {razorpay_order_id}\n'
          f'- Transaction ID: {payment_id}\n'
          f'- Status: Success\n\n'
          f'Your support drives our social trust initiatives forward.\n\n'
          f'Warm regards,\nBoys Foundation'
      )
      send_mail(
          receipt_subject,
          receipt_body,
          settings.DEFAULT_FROM_EMAIL,
          [donation.email],
          fail_silently=True,
      )
      # -----------------------------------------------------

      messages.success(
          request,
          f'Thank you, {donation.name}! Your donation of ₹{donation.amount} was'
          ' received successfully.',
      )
      return redirect('/donate/')

    except razorpay.errors.SignatureVerificationError:
      DonationPayment.objects.filter(razorpay_order_id=razorpay_order_id).update(
          status='Failed'
      )
      messages.error(request, 'Payment verification failed. Please try again.')
      return redirect('/donate/')
  else:
    return redirect('/donate/')


def contact(request):
  if request.method == 'POST':
    name = request.POST.get('name')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    subject = request.POST.get('subject')
    message = request.POST.get('message')

    ContactMessage.objects.create(
        name=name, email=email, phone=phone, subject=subject, message=message
    )

    # --- OPTION 1: SEND EMAILS FOR CONTACT FORM ---
    # 1. Thank-you email to user
    user_subject = 'Thank you for contacting Boys Foundation'
    user_body = (
        f'Dear {name},\n\nThank you for reaching out to Best One Young Society.'
        f' We have received your inquiry regarding "{subject}".\n\nOur team will'
        ' review your message and get back to you shortly.\n\nWarm'
        ' regards,\nBoys Foundation Team'
    )
    send_mail(
        user_subject,
        user_body,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=True,
    )

    # 2. Alert notification email to admin
    admin_subject = f'New Contact Inquiry: {subject}'
    admin_body = (
        f'You have received a new message from your website contact form:\n\n'
        f'Name: {name}\n'
        f'Email: {email}\n'
        f'Phone: {phone}\n'
        f'Subject: {subject}\n\n'
        f'Message:\n{message}'
    )
    send_mail(
        admin_subject,
        admin_body,
        settings.DEFAULT_FROM_EMAIL,
        ['boysfoundation2016@gmail.com'],
        fail_silently=True,
    )
    # ---------------------------------------------

    messages.success(request, 'Thank you! Your message has been sent successfully.')
    return redirect('/contact/')

  return render(request, 'portfolio/contact.html')