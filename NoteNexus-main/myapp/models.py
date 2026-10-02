import os

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.conf import settings


class UploadedNote(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('published', 'Published'),
        ('rejected', 'Rejected'),
    ]

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    uploader_name = models.CharField(max_length=120, blank=True)
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_notes',
    )
    uploader_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=120, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    cloudinary_public_id = models.CharField(max_length=255)
    cloudinary_resource_type = models.CharField(max_length=50, default='auto')
    document_url = models.URLField(max_length=1000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def file_extension(self):
        return os.path.splitext(self.original_filename)[1].lower().lstrip('.')

    @property
    def is_image(self):
        return self.file_extension in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    @property
    def is_pdf(self):
        return self.file_extension == 'pdf'

    @property
    def average_rating(self):
        average = self.ratings.aggregate(value=Avg('stars'))['value']
        return round(average or 0, 1)

    @property
    def rating_count(self):
        return self.ratings.count()

    @property
    def comment_count(self):
        return self.comments.count()


class NoteRating(models.Model):
    note = models.ForeignKey(UploadedNote, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='note_ratings')
    stars = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('note', 'user')

    def __str__(self):
        return f'{self.note} - {self.stars} stars'


class NoteComment(models.Model):
    note = models.ForeignKey(UploadedNote, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='note_comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.user} on {self.note}'


class ContactMessage(models.Model):

    SUBJECT_CHOICES = [
        ('support', 'Support'),
        ('billing', 'Billing'),
        ('partnership', 'Partnership'),
    ]

    name = models.CharField(max_length=100)

    email = models.EmailField()

    subject = models.CharField(
        max_length=50,
        choices=SUBJECT_CHOICES
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FeedbackMessage(models.Model):

    FEEDBACK_CHOICES = [
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
    ]

    feedback_type = models.CharField(
        max_length=20,
        choices=FEEDBACK_CHOICES
    )

    message = models.TextField()

    urgent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.feedback_type


class Doubt(models.Model):
    SUBJECT_CHOICES = [
        ('programming', 'Programming'),
        ('web_dev', 'Web Development'),
        ('database', 'Database'),
        ('dsa', 'Data Structures & Algorithms'),
        ('machine_learning', 'Machine Learning'),
        ('cloud', 'Cloud Computing'),
        ('devops', 'DevOps'),
        ('other', 'Other'),
    ]

    question = models.TextField()
    subject = models.CharField(
        max_length=50,
        choices=SUBJECT_CHOICES,
        default='other'
    )
    asked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doubts_asked'
    )
    instructor_response = models.TextField(
        blank=True,
        null=True
    )
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doubts_answered'
    )
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Doubt by {self.asked_by}: {self.question[:50]}'

    @property
    def reply_count(self):
        return self.replies.count()


class DoubtReply(models.Model):
    doubt = models.ForeignKey(
        Doubt,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doubt_replies'
    )
    reply_text = models.TextField()
    is_instructor_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Reply to {self.doubt.id} by {self.replied_by}'


class PYQ(models.Model):
    TYPE_CHOICES = [
        ('midterm', 'Midterm'),
        ('endterm', 'Endterm'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('other', 'Other'),
    ]

    paper_title = models.CharField(max_length=200)
    year = models.IntegerField(validators=[MinValueValidator(1990), MaxValueValidator(2100)])
    university = models.CharField(max_length=200)
    semester = models.CharField(max_length=50)
    pyq_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_pyqs'
    )
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=120, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    cloudinary_public_id = models.CharField(max_length=255)
    cloudinary_resource_type = models.CharField(max_length=50, default='auto')
    document_url = models.URLField(max_length=1000)
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year', '-created_at']

    def __str__(self):
        return f'{self.paper_title} - {self.year}'

    @property
    def file_extension(self):
        return os.path.splitext(self.original_filename)[1].lower().lstrip('.')

    @property
    def is_image(self):
        return self.file_extension in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    @property
    def is_pdf(self):
        return self.file_extension == 'pdf'

