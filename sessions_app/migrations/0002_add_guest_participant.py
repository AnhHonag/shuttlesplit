import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sessions_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GuestParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('amount_owed', models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ('is_paid', models.BooleanField(default=False)),
                ('note', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='guests',
                    to='sessions_app.badmintonsession',
                )),
            ],
            options={
                'verbose_name': 'Khách vãng lai',
                'ordering': ['created_at'],
            },
        ),
    ]
