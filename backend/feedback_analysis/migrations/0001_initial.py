# Generated migration for feedback_analysis models

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentication', '0001_add_work_item_candidate_table'),
        ('integrations', '0001_add_work_item_candidate_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('type', models.CharField(db_index=True, default='analysis', max_length=64)),
                ('analysis_type', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('quarter', models.CharField(blank=True, db_index=True, default='', max_length=32)),
                ('result', models.JSONField(blank=True, default=dict)),
                ('comments', models.JSONField(blank=True, default=list)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('project', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='integrations.project')),
                ('user', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='authentication.useraccount')),
            ],
            options={
                'db_table': 'analysis',
            },
        ),
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('type', models.CharField(db_index=True, default='upload', max_length=64)),
                ('filename', models.CharField(blank=True, default='', max_length=255)),
                ('content_type', models.CharField(blank=True, default='', max_length=128)),
                ('status', models.CharField(db_index=True, default='uploaded', max_length=32)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='authentication.useraccount')),
                ('project', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='integrations.project')),
            ],
            options={
                'db_table': 'uploads',
            },
        ),
        migrations.CreateModel(
            name='UserData',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('type', models.CharField(db_index=True, default='user_data', max_length=64)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='authentication.useraccount')),
                ('project', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='integrations.project')),
            ],
            options={
                'db_table': 'user_data',
            },
        ),
        migrations.CreateModel(
            name='Insight',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('type', models.CharField(db_index=True, default='insight', max_length=64)),
                ('analysis_type', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('analysis_date', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='authentication.useraccount')),
                ('project', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='integrations.project')),
            ],
            options={
                'db_table': 'insights',
            },
        ),
        migrations.CreateModel(
            name='Taxonomy',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('type', models.CharField(db_index=True, default='taxonomy', max_length=64)),
                ('version', models.IntegerField(db_index=True, default=1)),
                ('status', models.CharField(db_index=True, default='active', max_length=32)),
                ('is_pinned', models.BooleanField(db_index=True, default=False)),
                ('taxonomy', models.JSONField(blank=True, default=dict)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('project', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='integrations.project')),
            ],
            options={
                'db_table': 'taxonomies',
            },
        ),
        migrations.CreateModel(
            name='UsageRecord',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('type', models.CharField(db_index=True, default='usage', max_length=64)),
                ('endpoint', models.CharField(blank=True, db_index=True, default='', max_length=255)),
                ('count', models.IntegerField(default=0)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('project', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='integrations.project')),
                ('user', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='authentication.useraccount')),
            ],
            options={
                'db_table': 'usage',
            },
        ),
        migrations.CreateModel(
            name='CommentExtraction',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('type', models.CharField(db_index=True, default='comment_extraction', max_length=64)),
                ('source_type', models.CharField(blank=True, default='', max_length=64)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('project', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='integrations.project')),
                ('user', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='authentication.useraccount')),
            ],
            options={
                'db_table': 'comment_extractions',
            },
        ),
        migrations.CreateModel(
            name='InsightRule',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('type', models.CharField(db_index=True, default='insight_rule', max_length=64)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('project', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, to='integrations.project')),
            ],
            options={
                'db_table': 'insight_rules',
            },
        ),
        migrations.CreateModel(
            name='InsightReview',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('type', models.CharField(db_index=True, default='insight_review', max_length=64)),
                ('status', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('project', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, to='integrations.project')),
            ],
            options={
                'db_table': 'insight_reviews',
            },
        ),
        migrations.CreateModel(
            name='IngestionSchedule',
            fields=[
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('type', models.CharField(db_index=True, default='ingestion_schedule', max_length=64)),
                ('status', models.CharField(db_index=True, default='active', max_length=32)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('project', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='integrations.project')),
            ],
            options={
                'db_table': 'ingestion_schedules',
            },
        ),
        migrations.AddIndex(
            model_name='analysis',
            index=models.Index(fields=['project', 'created_at'], name='analysis_project_created_idx'),
        ),
        migrations.AddIndex(
            model_name='analysis',
            index=models.Index(fields=['user', 'created_at'], name='analysis_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='analysis',
            index=models.Index(fields=['type', 'created_at'], name='analysis_type_created_idx'),
        ),
        migrations.AddConstraint(
            model_name='insightrule',
            constraint=models.UniqueConstraint(fields=('project',), name='uq_insight_rule_project'),
        ),
    ]
