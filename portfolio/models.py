from django.db import models

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='projects/', blank=True, null=True)
    date_posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"

class DonationPayment(models.Model):
  name = models.CharField(max_length=100)
  email = models.EmailField()
  amount = models.IntegerField()  # Amount in INR
  razorpay_order_id = models.CharField(max_length=100, unique=True)
  razorpay_payment_id = models.CharField(
      max_length=100, blank=True, null=True
  )
  razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
  status = models.CharField(
      max_length=20, default='Pending'
  )  # Pending, Success, Failed
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f'{self.name} - ₹{self.amount} ({self.status})'