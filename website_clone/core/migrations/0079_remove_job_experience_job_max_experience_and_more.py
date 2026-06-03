from django.db import migrations, models
import json


def convert_skills_to_json(apps, schema_editor):
    """
    Runs BEFORE the column type changes.
    Reads each job's skills string like "python, django, sql"
    and converts it to a JSON string: '["python", "django", "sql"]'
    so PostgreSQL can safely cast it to JSONField.
    """
    Job = apps.get_model('core', 'Job')
    for job in Job.objects.all():
        if job.skills:
            # Split the comma-separated string into a list
            skills_list = [s.strip() for s in job.skills.split(',') if s.strip()]
        else:
            skills_list = []
        # Save it back as a JSON string
        job.skills = json.dumps(skills_list)
        job.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0078_alter_job_location'),
    ]
    
    operations = [
        # Step 1: Convert existing string data to JSON strings FIRST
        migrations.RunPython(convert_skills_to_json, migrations.RunPython.noop),

        # Step 2: NOW safely change the column type to JSONField
        migrations.AlterField(
            model_name='job',
            name='skills',
            field=models.JSONField(default=list),
        ),

        # Step 3: Remove old experience CharField
        migrations.RemoveField(
            model_name='job',
            name='experience',
        ),

        # Step 4: Add new experience IntegerFields
        migrations.AddField(
            model_name='job',
            name='min_experience',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='job',
            name='max_experience',
            field=models.IntegerField(default=5),
        ),
    ]