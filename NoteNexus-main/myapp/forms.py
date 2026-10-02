import os

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class NoteUploadForm(forms.Form):
    ALLOWED_EXTENSIONS = {
        '.pdf',
        '.png',
        '.jpg',
        '.jpeg',
        '.gif',
        '.webp',
        '.doc',
        '.docx',
        '.ppt',
        '.pptx',
        '.xls',
        '.xlsx',
        '.txt',
        '.zip',
    }

    title = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Note title',
                'required': True,
            }
        ),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Brief note description',
                'rows': 4,
            }
        ),
    )
    uploader_name = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Your name',
            }
        ),
    )
    document = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                'accept': '.pdf,.png,.jpg,.jpeg,.gif,.webp,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.zip',
                'required': True,
            }
        )
    )

    def clean_document(self):
        document = self.cleaned_data['document']
        extension = os.path.splitext(document.name)[1].lower()

        if extension not in self.ALLOWED_EXTENSIONS:
            raise forms.ValidationError('Upload a PDF, image, document, spreadsheet, presentation, text, or zip file.')

        max_size = 25 * 1024 * 1024
        if document.size > max_size:
            raise forms.ValidationError('File size must be 25 MB or less.')

        return document


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email', 'required': True}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password', 'required': True}),
    )


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email', 'required': True}),
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First name', 'required': True}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Last name', 'required': True}),
    )
    role = forms.ChoiceField(
        choices=[
            ('student', 'Student'),
            ('instructor', 'Instructor'),
        ],
        widget=forms.Select(attrs={'required': True}),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Assign to group based on role
            from django.contrib.auth.models import Group
            role = self.cleaned_data['role']
            if role == 'student':
                group, _ = Group.objects.get_or_create(name='Students')
            elif role == 'instructor':
                group, _ = Group.objects.get_or_create(name='Instructors')
            user.groups.add(group)
        return user


class ContactForm(forms.Form):
    title = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Note title',
                'required': True,
            }
        ),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Brief note description',
                'rows': 4,
            }
        ),
    )
    uploader_name = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Your name',
            }
        ),
    )
    document = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                'accept': '.pdf,.doc,.docx,.ppt,.pptx,.txt',
                'required': True,
            }
        )
    )


class ContactForm(forms.Form):
    from_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'John Doe', 'required': True}),
    )
    reply_to = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'john@example.com', 'required': True}),
    )
    subject = forms.ChoiceField(
        choices=[
            ('support', 'General Support'),
            ('billing', 'Billing Inquiry'),
            ('partnership', 'Partnership'),
        ],
        widget=forms.Select(attrs={'required': True}),
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'How can we help you?', 'rows': 6, 'required': True}),
    )


class FeedbackForm(forms.Form):
    feedback_type = forms.ChoiceField(
        choices=[
            ('bug', 'Bug Report'),
            ('feature', 'Feature Request'),
            ('general', 'General Feedback'),
        ],
        widget=forms.RadioSelect,
        initial='feature',
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Your feedback is most important to us...', 'rows': 6, 'required': True}),
    )
    urgent = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(),
    )


class DoubtForm(forms.Form):
    question = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Ask your question here...',
                'rows': 5,
                'required': True,
            }
        ),
    )
    subject = forms.ChoiceField(
        choices=[
            ('programming', 'Programming'),
            ('web_dev', 'Web Development'),
            ('database', 'Database'),
            ('dsa', 'Data Structures & Algorithms'),
            ('machine_learning', 'Machine Learning'),
            ('cloud', 'Cloud Computing'),
            ('devops', 'DevOps'),
            ('other', 'Other'),
        ],
        widget=forms.Select(
            attrs={
                'required': True,
            }
        ),
    )


class DoubtReplyForm(forms.Form):
    reply_text = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Write your reply here...',
                'rows': 3,
                'required': True,
            }
        ),
    )


class PYQUploadForm(forms.Form):
    ALLOWED_EXTENSIONS = {
        '.pdf',
        '.png',
        '.jpg',
        '.jpeg',
        '.gif',
        '.webp',
        '.doc',
        '.docx',
        '.ppt',
        '.pptx',
        '.txt',
        '.zip',
    }

    paper_title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'e.g. Data Structures Final Exam',
                'required': True,
            }
        ),
    )
    year = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                'placeholder': '2024',
                'required': True,
                'min': 1990,
                'max': 2100,
            }
        ),
    )
    university = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'e.g. Delhi University',
                'required': True,
            }
        ),
    )
    semester = forms.CharField(
        max_length=50,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'e.g. Sem 4',
                'required': True,
            }
        ),
    )
    pyq_type = forms.ChoiceField(
        choices=[
            ('midterm', 'Midterm'),
            ('endterm', 'Endterm'),
            ('quiz', 'Quiz'),
            ('assignment', 'Assignment'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'required': True}),
    )
    document = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                'accept': '.pdf,.png,.jpg,.jpeg,.gif,.webp,.doc,.docx,.ppt,.pptx,.txt,.zip',
                'required': True,
            }
        )
    )

    def clean_document(self):
        document = self.cleaned_data['document']
        extension = os.path.splitext(document.name)[1].lower()

        if extension not in self.ALLOWED_EXTENSIONS:
            raise forms.ValidationError('Upload a PDF, image, document, or zip file.')

        max_size = 25 * 1024 * 1024
        if document.size > max_size:
            raise forms.ValidationError('File size must be 25 MB or less.')

        return document


# Email forms for Brevo SMTP integration

class SendProfileEmailForm(forms.Form):
    """Form for sending emails to user/instructor profiles."""
    
    to_email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'recipient@example.com',
                'required': True,
                'class': 'form-control',
            }
        ),
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Email subject',
                'required': True,
                'class': 'form-control',
            }
        ),
    )
    
    message = forms.CharField(
        max_length=5000,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Your message (minimum 10 characters, maximum 5000)',
                'rows': 8,
                'required': True,
                'class': 'form-control',
            }
        ),
    )
    
    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '').strip()
        if not subject:
            raise forms.ValidationError('Subject is required.')
        if len(subject) < 3:
            raise forms.ValidationError('Subject must be at least 3 characters.')
        if len(subject) > 200:
            raise forms.ValidationError('Subject cannot exceed 200 characters.')
        return subject
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if not message:
            raise forms.ValidationError('Message is required.')
        if len(message) < 10:
            raise forms.ValidationError('Message must be at least 10 characters.')
        if len(message) > 5000:
            raise forms.ValidationError('Message cannot exceed 5000 characters.')
        return message


class ContactProfileForm(forms.Form):
    """Form for contacting a specific user/instructor profile."""
    
    recipient_email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Recipient email address',
                'required': True,
                'readonly': True,
                'class': 'form-control',
            }
        ),
    )
    
    sender_email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Your email address',
                'required': True,
                'class': 'form-control',
            }
        ),
    )
    
    sender_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Your name',
                'required': True,
                'class': 'form-control',
            }
        ),
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Email subject',
                'required': True,
                'class': 'form-control',
            }
        ),
    )
    
    message = forms.CharField(
        max_length=5000,
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Your message (minimum 10 characters, maximum 5000)',
                'rows': 8,
                'required': True,
                'class': 'form-control',
            }
        ),
    )
    
    def clean_sender_name(self):
        name = self.cleaned_data.get('sender_name', '').strip()
        if not name:
            raise forms.ValidationError('Your name is required.')
        if len(name) < 2:
            raise forms.ValidationError('Name must be at least 2 characters.')
        if len(name) > 100:
            raise forms.ValidationError('Name cannot exceed 100 characters.')
        return name
    
    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '').strip()
        if not subject:
            raise forms.ValidationError('Subject is required.')
        if len(subject) < 3:
            raise forms.ValidationError('Subject must be at least 3 characters.')
        if len(subject) > 200:
            raise forms.ValidationError('Subject cannot exceed 200 characters.')
        return subject
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if not message:
            raise forms.ValidationError('Message is required.')
        if len(message) < 10:
            raise forms.ValidationError('Message must be at least 10 characters.')
        if len(message) > 5000:
            raise forms.ValidationError('Message cannot exceed 5000 characters.')
        return message
    
    def clean(self):
        cleaned_data = super().clean()
        sender_email = cleaned_data.get('sender_email')
        recipient_email = cleaned_data.get('recipient_email')
        
        if sender_email and recipient_email:
            if sender_email.lower() == recipient_email.lower():
                raise forms.ValidationError('You cannot send an email to yourself.')
        
        return cleaned_data
