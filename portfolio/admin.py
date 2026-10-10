from django.contrib import admin
from .models import Project, ContactMessage, DonationPayment

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_posted')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'date_sent')

@admin.register(DonationPayment)
class DonationPaymentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'amount', 'status', 'created_at')