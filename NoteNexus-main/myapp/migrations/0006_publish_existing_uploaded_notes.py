from django.db import migrations


def publish_existing_notes(apps, schema_editor):
    UploadedNote = apps.get_model('myapp', 'UploadedNote')
    UploadedNote.objects.filter(status='pending').update(status='published')


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_uploadednote_download_count_uploadednote_view_count_and_more'),
    ]

    operations = [
        migrations.RunPython(publish_existing_notes, migrations.RunPython.noop),
    ]
