import cloudinary
import cloudinary.uploader

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import Group, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db.models import Q

from .forms import ContactForm, FeedbackForm, NoteUploadForm, DoubtForm, DoubtReplyForm
from .models import ContactMessage, FeedbackMessage, NoteComment, NoteRating, UploadedNote, Doubt, DoubtReply, PYQ
from .forms import SendProfileEmailForm
from .email_utils import send_confirmation_email, send_profile_contact_email

def home(request):
    return render(request, 'myapp/home.html') 


def base(request):
    return render(request, 'myapp/base.html')


def _dashboard_for(user):
    if user.groups.filter(name='Instructors').exists():
        return 'instructor'
    return 'user'


def _display_name(user):
    return user.get_full_name() or user.username


def _profile_context(request, role_label):
    uploads = UploadedNote.objects.filter(uploader=request.user)
    return {
        'display_name': _display_name(request.user),
        'initials': ''.join(part[:1] for part in _display_name(request.user).split()[:2]).upper() or 'U',
        'role_label': role_label,
        'joined_date': request.user.date_joined,
        'profile_stats': {
            'notes_uploaded': uploads.count(),
            'downloads': sum(note.download_count for note in uploads),
            'views': sum(note.view_count for note in uploads),
        },
        'password_form': PasswordChangeForm(request.user),
    }


def _handle_profile_post(request):
    action = request.POST.get('action')

    if action == 'update_profile':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()

        if not full_name or not email:
            messages.error(request, 'Name and email are required.')
            return

        if User.objects.filter(email__iexact=email).exclude(pk=request.user.pk).exists():
            messages.error(request, 'That email is already used by another account.')
            return

        name_parts = full_name.split(maxsplit=1)
        request.user.first_name = name_parts[0]
        request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        request.user.email = email
        request.user.username = email
        request.user.save(update_fields=['first_name', 'last_name', 'email', 'username'])
        messages.success(request, 'Profile updated successfully.')

    elif action == 'change_password':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password updated successfully.')
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)

    elif action == 'send_email':
        email_form = SendProfileEmailForm(request.POST)
        if email_form.is_valid():
            to_email = email_form.cleaned_data['to_email']
            subject = email_form.cleaned_data['subject']
            message = email_form.cleaned_data['message']
            
            result = send_profile_contact_email(
                recipient_email=to_email,
                sender_name=request.user.get_full_name() or request.user.username,
                sender_email=request.user.email,
                subject=subject,
                message=message,
            )
            
            if result.get('success'):
                send_confirmation_email(request.user.email, request.user.get_full_name() or request.user.username)
                messages.success(request, 'Your email has been sent successfully!')
            else:
                error_message = result.get('message') or 'Unknown error'
                if result.get('suggested_action'):
                    error_message = f'{error_message} {result["suggested_action"]}'
                messages.error(request, f'Failed to send email: {error_message}')
        else:
            for field, errors in email_form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')


def _dashboard_stats():
    return {
        'total_notes': UploadedNote.objects.count(),
        'student_notes': UploadedNote.objects.filter(uploader_role='student').count(),
        'instructor_notes': UploadedNote.objects.filter(uploader_role='instructor').count(),
        'pending_notes': UploadedNote.objects.filter(status='pending').count(),
    }


def _available_notes():
    return UploadedNote.objects.filter(status='published').prefetch_related('ratings', 'comments__user')


def _cloudinary_is_configured():
    cloudinary_settings = settings.CLOUDINARY
    return all([
        cloudinary_settings.get('cloud_name'),
        cloudinary_settings.get('api_key'),
        cloudinary_settings.get('api_secret'),
        cloudinary_settings.get('cloud_name') != 'your_cloud_name',
        cloudinary_settings.get('api_key') != 'your_api_key',
        cloudinary_settings.get('api_secret') != 'your_api_secret',
    ])


def _upload_note_to_cloudinary(request, uploader_role):
    form = NoteUploadForm(request.POST, request.FILES)

    if not form.is_valid():
        messages.error(request, 'Please correct the upload form and try again.')
        return form, None

    if not _cloudinary_is_configured():
        messages.error(
            request,
            'Cloudinary is not configured. Add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET to your .env file.',
        )
        return form, None

    cloudinary.config(
        cloud_name=settings.CLOUDINARY['cloud_name'],
        api_key=settings.CLOUDINARY['api_key'],
        api_secret=settings.CLOUDINARY['api_secret'],
        secure=True,
    )

    document = form.cleaned_data['document']
    try:
        upload_result = cloudinary.uploader.upload(
            document,
            folder=f'notenexus/{uploader_role}-notes',
            resource_type='auto',
            use_filename=True,
            unique_filename=True,
        )
    except Exception as error:
        messages.error(request, f'Cloudinary upload failed: {error}')
        return form, None

    note = UploadedNote.objects.create(
        title=form.cleaned_data['title'],
        description=form.cleaned_data['description'],
        uploader_name=form.cleaned_data['uploader_name'] or request.user.get_full_name() or request.user.username,
        uploader=request.user,
        uploader_role=uploader_role,
        original_filename=document.name,
        file_type=document.content_type or '',
        file_size=document.size,
        cloudinary_public_id=upload_result['public_id'],
        cloudinary_resource_type=upload_result.get('resource_type', 'auto'),
        document_url=upload_result['secure_url'],
        status='published' if uploader_role == 'instructor' else 'pending',
    )

    if uploader_role == 'student':
        messages.success(request, 'Note uploaded successfully and sent for instructor review.')
    else:
        messages.success(request, 'Note uploaded successfully.')
    return NoteUploadForm(), note


def _handle_note_feedback(request):
    note = get_object_or_404(UploadedNote, pk=request.POST.get('note_id'), status='published')
    stars = request.POST.get('stars')
    comment = request.POST.get('comment', '').strip()

    if stars:
        try:
            stars = int(stars)
        except ValueError:
            stars = 0

        if 1 <= stars <= 5:
            NoteRating.objects.update_or_create(
                note=note,
                user=request.user,
                defaults={'stars': stars},
            )
        else:
            messages.error(request, 'Please choose a star rating from 1 to 5.')
            return

    if comment:
        NoteComment.objects.create(note=note, user=request.user, comment=comment)

    if stars or comment:
        messages.success(request, 'Your feedback was saved.')
    else:
        messages.error(request, 'Add a star rating or comment before submitting.')


def _upload_pyq_to_cloudinary(request):
    from .forms import PYQUploadForm
    from .models import PYQ
    
    form = PYQUploadForm(request.POST, request.FILES)

    if not form.is_valid():
        messages.error(request, 'Please correct the PYQ upload form and try again.')
        return form, None

    if not _cloudinary_is_configured():
        messages.error(
            request,
            'Cloudinary is not configured. Add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET to your .env file.',
        )
        return form, None

    cloudinary.config(
        cloud_name=settings.CLOUDINARY['cloud_name'],
        api_key=settings.CLOUDINARY['api_key'],
        api_secret=settings.CLOUDINARY['api_secret'],
        secure=True,
    )

    document = form.cleaned_data['document']
    try:
        upload_result = cloudinary.uploader.upload(
            document,
            folder='notenexus/pyqs',
            resource_type='auto',
            use_filename=True,
            unique_filename=True,
        )
    except Exception as error:
        messages.error(request, f'Cloudinary upload failed: {error}')
        return form, None

    pyq = PYQ.objects.create(
        paper_title=form.cleaned_data['paper_title'],
        year=form.cleaned_data['year'],
        university=form.cleaned_data['university'],
        semester=form.cleaned_data['semester'],
        pyq_type=form.cleaned_data['pyq_type'],
        uploader=request.user,
        original_filename=document.name,
        file_type=document.content_type or '',
        file_size=document.size,
        cloudinary_public_id=upload_result['public_id'],
        cloudinary_resource_type=upload_result.get('resource_type', 'auto'),
        document_url=upload_result['secure_url'],
    )

    messages.success(request, 'PYQ uploaded successfully.')
    return PYQUploadForm(), pyq


def _handle_note_delete(request):
    note = get_object_or_404(UploadedNote, pk=request.POST.get('note_id'), uploader=request.user)

    if _cloudinary_is_configured() and note.cloudinary_public_id:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY['cloud_name'],
            api_key=settings.CLOUDINARY['api_key'],
            api_secret=settings.CLOUDINARY['api_secret'],
            secure=True,
        )
        try:
            cloudinary.uploader.destroy(
                note.cloudinary_public_id,
                resource_type=note.cloudinary_resource_type or 'raw',
            )
        except Exception as error:
            messages.warning(request, f'Cloudinary delete failed, but the note was removed from the site: {error}')

    note.delete()
    messages.success(request, 'Your uploaded note was deleted.')


def _handle_student_upload_review(request):
    note = get_object_or_404(
        UploadedNote,
        pk=request.POST.get('note_id'),
        uploader_role='student',
        status='pending',
    )
    review_action = request.POST.get('review_action')

    if review_action == 'approve':
        note.status = 'published'
        note.save(update_fields=['status'])
        messages.success(request, f'"{note.title}" was approved and is now available.')
    elif review_action == 'reject':
        note.status = 'rejected'
        note.save(update_fields=['status'])
        messages.success(request, f'"{note.title}" was rejected.')
    else:
        messages.error(request, 'Choose approve or reject for the upload.')


def _handle_doubt_reply(request):
    doubt_id = request.POST.get('doubt_id')
    reply_text = request.POST.get('reply_text', '').strip()

    if not doubt_id or not reply_text:
        messages.error(request, 'Please provide a reply.')
        return

    doubt = get_object_or_404(Doubt, pk=doubt_id)
    is_instructor = request.user.groups.filter(name='Instructors').exists()

    DoubtReply.objects.create(
        doubt=doubt,
        replied_by=request.user,
        reply_text=reply_text,
        is_instructor_reply=is_instructor,
    )

    messages.success(request, 'Your reply has been posted.')


def _handle_mark_doubt_solved(request):
    doubt_id = request.POST.get('doubt_id')

    if not doubt_id:
        messages.error(request, 'Invalid request.')
        return

    doubt = get_object_or_404(Doubt, pk=doubt_id)
    
    # Only the person who asked the question can mark it as solved
    if doubt.asked_by != request.user:
        messages.error(request, 'You can only mark your own questions as solved.')
        return

    doubt.is_answered = True
    doubt.save()
    messages.success(request, 'Question marked as solved!')


def _handle_unmark_doubt_solved(request):
    doubt_id = request.POST.get('doubt_id')

    if not doubt_id:
        messages.error(request, 'Invalid request.')
        return

    doubt = get_object_or_404(Doubt, pk=doubt_id)
    
    # Only the person who asked the question can unmark it as solved
    if doubt.asked_by != request.user:
        messages.error(request, 'You can only change your own questions.')
        return

    doubt.is_answered = False
    doubt.save()
    messages.success(request, 'Question marked as unresolved!')


@never_cache
def auth_view(request):
    if request.user.is_authenticated and request.method != 'POST':
        return redirect(_dashboard_for(request.user))

    active_tab = request.GET.get('tab', 'login')

    if request.method == 'POST':
        if request.user.is_authenticated:
            logout(request)

        action = request.POST.get('action')
        active_tab = action or active_tab

        if action == 'login':
            email = request.POST.get('email', '').strip().lower()
            password = request.POST.get('password', '')

            user = authenticate(request, username=email, password=password)
            if user is None:
                existing_user = User.objects.filter(email__iexact=email).first()
                if existing_user:
                    user = authenticate(request, username=existing_user.username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful.')
                return redirect(_dashboard_for(user))

            messages.error(request, 'Invalid email or password.')

        elif action == 'signup':
            full_name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip().lower()
            password = request.POST.get('password', '')
            role = request.POST.get('role', 'user')

            if not full_name or not email or not password:
                messages.error(request, 'Please fill in all signup fields.')
            elif User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
                messages.error(request, 'An account with this email already exists.')
            else:
                user = User(username=email, email=email)
                name_parts = full_name.split(maxsplit=1)
                user.first_name = name_parts[0]
                user.last_name = name_parts[1] if len(name_parts) > 1 else ''

                try:
                    validate_password(password, user)
                except ValidationError as error:
                    for message in error.messages:
                        messages.error(request, message)
                else:
                    user.set_password(password)
                    user.save()

                    group_name = 'Instructors' if role == 'instructor' else 'Students'
                    group, _ = Group.objects.get_or_create(name=group_name)
                    user.groups.add(group)

                    login(request, user)
                    messages.success(request, 'Account created successfully.')
                    return redirect(_dashboard_for(user))
        else:
            messages.error(request, 'Please choose login or signup.')

    return render(request, 'myapp/auth.html', {'active_tab': active_tab})


def login_view(request):
    return redirect('auth')


def signup_view(request):
    return redirect('/auth/?tab=signup')


@never_cache
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required(login_url='auth')
@never_cache
def instructor_dashboard_view(request):   
    if not request.user.groups.filter(name='Instructors').exists():
        messages.error(request, 'Please login as an instructor to access that page.')
        return redirect('auth')

    note_form = NoteUploadForm()
    upload_success = None

    if request.method == 'POST' and request.POST.get('action') == 'note_feedback':
        _handle_note_feedback(request)
        return redirect('instructor')

    if request.method == 'POST' and request.POST.get('action') == 'delete_note':
        _handle_note_delete(request)
        return redirect('instructor')

    if request.method == 'POST' and request.POST.get('action') == 'review_student_upload':
        _handle_student_upload_review(request)
        return redirect('instructor')

    if request.method == 'POST' and request.POST.get('action') == 'reply_doubt':
        _handle_doubt_reply(request)
        return redirect('instructor')

    if request.method == 'POST' and request.POST.get('action') == 'mark_doubt_solved':
        _handle_mark_doubt_solved(request)
        return redirect('instructor')

    if request.method == 'POST' and request.POST.get('action') == 'unmark_doubt_solved':
        _handle_unmark_doubt_solved(request)
        return redirect('instructor')

    if request.method == 'POST':
        note_form, upload_success = _upload_note_to_cloudinary(request, 'instructor')

    return render(request, 'myapp/instructor_dashboard.html', {
        'note_form': note_form,
        'upload_success': upload_success,
        'dashboard_stats': _dashboard_stats(),
        'my_uploads': UploadedNote.objects.filter(uploader=request.user)[:5],
        'pending_student_uploads': UploadedNote.objects.filter(uploader_role='student', status='pending')[:10],
        'available_notes': _available_notes()[:10],
        'available_pyqs': PYQ.objects.all()[:10],
        'community_doubts': Doubt.objects.all()[:15],
    })


@login_required(login_url='auth')
@never_cache
def user_dashboard_view(request):
    from .models import PYQ
    from .forms import PYQUploadForm
    
    note_form = NoteUploadForm()
    pyq_form = PYQUploadForm()
    upload_success = None
    pyq_upload_success = None

    if request.method == 'POST' and request.POST.get('action') == 'note_feedback':
        _handle_note_feedback(request)
        return redirect('user')

    if request.method == 'POST' and request.POST.get('action') == 'delete_note':
        _handle_note_delete(request)
        return redirect('user')

    if request.method == 'POST' and request.POST.get('action') == 'reply_doubt':
        _handle_doubt_reply(request)
        return redirect('user')

    if request.method == 'POST' and request.POST.get('action') == 'mark_doubt_solved':
        _handle_mark_doubt_solved(request)
        return redirect('user')

    if request.method == 'POST' and request.POST.get('action') == 'unmark_doubt_solved':
        _handle_unmark_doubt_solved(request)
        return redirect('user')

    if request.method == 'POST' and request.POST.get('action') != 'upload_pyq':
        note_form, upload_success = _upload_note_to_cloudinary(request, 'student')

    if request.method == 'POST' and request.POST.get('action') == 'upload_pyq':
        pyq_form, pyq_upload_success = _upload_pyq_to_cloudinary(request)

    return render(request, 'myapp/user_dashboard.html', {
        'note_form': note_form,
        'pyq_form': pyq_form,
        'upload_success': upload_success,
        'pyq_upload_success': pyq_upload_success,
        'dashboard_stats': _dashboard_stats(),
        'my_uploads': UploadedNote.objects.filter(uploader=request.user)[:5],
        'my_pyqs': PYQ.objects.filter(uploader=request.user)[:5],
        'available_notes': _available_notes()[:10],
        'available_pyqs': PYQ.objects.all()[:10],
        'community_doubts': Doubt.objects.all()[:15],
    })


@login_required(login_url='auth')
@xframe_options_sameorigin
def note_view_redirect(request, note_id):
    note = get_object_or_404(UploadedNote, pk=note_id)
    can_preview = (
        note.status == 'published'
        or note.uploader_id == request.user.id
        or request.user.groups.filter(name='Instructors').exists()
    )
    if not can_preview:
        raise Http404
    UploadedNote.objects.filter(pk=note.pk).update(view_count=F('view_count') + 1)
    note.refresh_from_db(fields=['view_count'])
    return render(request, 'myapp/note_preview.html', {'note': note})


@login_required(login_url='auth')
def note_download_redirect(request, note_id):
    note = get_object_or_404(UploadedNote, pk=note_id, status='published')
    UploadedNote.objects.filter(pk=note.pk).update(download_count=F('download_count') + 1)
    return redirect(note.document_url)


def pyq_download_redirect(request, pyq_id):
    from .models import PYQ
    pyq = get_object_or_404(PYQ, pk=pyq_id)
    PYQ.objects.filter(pk=pyq.pk).update(download_count=F('download_count') + 1)
    return redirect(pyq.document_url)


@login_required(login_url='auth')
@never_cache
def user_profile_view(request):
    if request.method == 'POST':
        _handle_profile_post(request)
        return redirect('user_profile')

    return render(request, 'myapp/user_profile.html', _profile_context(request, 'Student'))


@login_required(login_url='auth')
@never_cache
def instructor_profile_view(request):
    if request.method == 'POST':
        _handle_profile_post(request)
        return redirect('instructor_profile')

    return render(request, 'myapp/instructor_profile.html', _profile_context(request, 'Instructor'))


def about_view(request):
    contact_form = ContactForm(request.POST or None, prefix='contact')
    feedback_form = FeedbackForm(request.POST or None, prefix='feedback')

    if request.method == 'POST':
        if 'contact-submit' in request.POST and contact_form.is_valid():
            ContactMessage.objects.create(
                name=contact_form.cleaned_data['from_name'],
                email=contact_form.cleaned_data['reply_to'],
                subject=contact_form.cleaned_data['subject'],
                message=contact_form.cleaned_data['message'],
            )
            messages.success(request, 'Your message has been received. We will get back to you shortly.')
            contact_form = ContactForm(prefix='contact')
        elif 'feedback-submit' in request.POST and feedback_form.is_valid():
            FeedbackMessage.objects.create(
                feedback_type=feedback_form.cleaned_data['feedback_type'],
                message=feedback_form.cleaned_data['message'],
                urgent=feedback_form.cleaned_data['urgent'],
            )
            messages.success(request, 'Thank you for your feedback. Our team will review it soon.')
            feedback_form = FeedbackForm(prefix='feedback')

    return render(request, 'myapp/about.html', {
        'contact_form': contact_form,
        'feedback_form': feedback_form,
    })


@login_required(login_url='auth')
def ask_doubt_view(request):
    if request.method == 'POST':
        form = DoubtForm(request.POST)
        if form.is_valid():
            doubt = Doubt.objects.create(
                question=form.cleaned_data['question'],
                subject=form.cleaned_data['subject'],
                asked_by=request.user,
            )
            return redirect(request.POST.get('next', 'user'))
    
    form = DoubtForm()
    return render(request, 'myapp/ask_doubt.html', {'form': form})


def user_dashboard(request):

    search_query = request.GET.get('search', '')
    sort_option = request.GET.get('sort', 'latest')

    notes = UploadedNote.objects.filter(status='published')

    # SEARCH
    if search_query:
        notes = notes.filter(
            Q(title__icontains=search_query) |
            Q(uploader_name__icontains=search_query)
        )

    # SORTING
    if sort_option == 'popular':
        notes = notes.order_by('-download_count')
    else:
        notes = notes.order_by('-created_at')

    context = {
        'notes': notes,
    }

    return render(request, 'myapp/user_dashboard.html', context)
