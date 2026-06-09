from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='receipt_image',
            field=models.FileField(blank=True, null=True, upload_to='receipts/'),
        ),
    ]
