from django.db import models

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='projects/', blank=True, null=True)  # Main/featured cover image
    date_posted = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0, help_text="Set custom order (1 = first, 2 = second, etc.)")

    class Meta:
        ordering = ['order', '-date_posted']

    def __str__(self):
        return self.title


class ProjectImage(models.Model):
    """Allows uploading multiple additional images for a single project"""
    project = models.ForeignKey(Project, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='projects/gallery/')
    caption = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Image for {self.project.title}"


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

class BloodDonor(models.Model):
    BLOOD_GROUPS = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS)
    location = models.CharField(max_length=100, default='Kovur')
    date_registered = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_registered']

    def __str__(self):
        return f"{self.name} ({self.blood_group}) - {self.location}"

# --- TEAM MEMBERS MODEL ---
class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)  # e.g., Founder, Coordinator, Volunteer Lead
    image = models.ImageField(upload_to='team/', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} - {self.role}"


# --- AWARDS & RECOGNITION MODEL ---
class Award(models.Model):
    title = models.CharField(max_length=200) # e.g., Best Youth NGO Award
    issued_by = models.CharField(max_length=200, blank=True, null=True) # e.g., District Collectorate / Lions Club
    year = models.CharField(max_length=10, blank=True, null=True) # e.g., 2025
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='awards/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', '-year']

    def __str__(self):
        return self.title