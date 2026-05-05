import uuid
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RefreshToken',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('token_hash', models.CharField(db_index=True, max_length=255)),
                ('expires_at', models.DateTimeField()),
                ('revoked', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(null=True, blank=True)),
                ('user_agent', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='refresh_tokens', to='users.user')),
            ],
            options={
                'db_table': 'refresh_tokens',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='refreshtoken',
            index=models.Index(fields=['token_hash'], name='refresh_tok_token_ha_3c7e5f_idx'),
        ),
        migrations.AddIndex(
            model_name='refreshtoken',
            index=models.Index(fields=['expires_at'], name='refresh_tok_expires__8a9f3c_idx'),
        ),
        migrations.AddIndex(
            model_name='refreshtoken',
            index=models.Index(fields=['revoked'], name='refresh_tok_revoked_2b8d4a_idx'),
        ),
    ]
