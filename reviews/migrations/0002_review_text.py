# Generated by Django 5.0.3 on 2024-03-21 05:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='text',
            field=models.TextField(default='lol', max_length=250),
            preserve_default=False,
        ),
    ]
