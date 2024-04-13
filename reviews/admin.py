from django.contrib import admin
from .models import Review, Reply

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    pass

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    pass