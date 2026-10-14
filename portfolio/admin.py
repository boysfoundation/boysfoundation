from django.contrib import admin
from .models import Project, ProjectImage, ContactMessage, DonationPayment
from .models import BloodDonor
from .models import TeamMember, Award  # plus your existing Project model
from .models import Event

admin.site.site_header = "Boys Foundation Administration"
admin.site.site_title = "Boys Foundation Portal"
admin.site.index_title = "Welcome to Boys Foundation Dashboard"

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

@admin.register(BloodDonor)
class BloodDonorAdmin(admin.ModelAdmin):
    list_display = ('name', 'blood_group', 'phone', 'location', 'date_registered')
    list_filter = ('blood_group', 'location')
    search_fields = ('name', 'phone', 'location')

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'display_order')
    list_editable = ('display_order',)
    search_fields = ('name', 'role')

@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = ('title', 'issued_by', 'year', 'display_order')
    list_editable = ('display_order',)
    search_fields = ('title', 'issued_by')


admin.site.register(Event)