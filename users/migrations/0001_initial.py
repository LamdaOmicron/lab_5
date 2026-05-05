import uuid
from django.db import models, migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('email', models.EmailField(unique=True, max_length=254, null=True, blank=True)),
                ('phone', models.CharField(unique=True, max_length=20, null=True, blank=True)),
                ('password_hash', models.CharField(max_length=255, null=True, blank=True)),
                ('salt', models.CharField(max_length=255, null=True, blank=True)),
                ('yandex_id', models.CharField(db_index=True, max_length=255, null=True, blank=True)),
                ('vk_id', models.CharField(db_index=True, max_length=255, null=True, blank=True)),
                ('first_name', models.CharField(blank=True, max_length=100)),
                ('last_name', models.CharField(blank=True, max_length=100)),
                ('avatar_url', models.URLField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'db_table': 'users',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['deleted_at'], name='users_delet_bf8c39_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='users_email_1d9e06_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['phone'], name='users_phone_a3da76_idx'),
        ),
    ]
