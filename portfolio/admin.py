from django.contrib import admin
from .models import Project, ProjectImage, ContactMessage, DonationPayment

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 3  # Displays 3 empty upload slots by default for additional images

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'date_posted')
    list_editable = ('order',)  # Allows changing position numbers directly from the list view!
    inlines = [ProjectImageInline]

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'date_sent')

@admin.register(DonationPayment)
class DonationPaymentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'amount', 'status', 'created_at')