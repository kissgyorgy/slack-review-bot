# Generated by Django 2.1.2 on 2018-10-31 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slackbot', '0003_auto_20180304_1931'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crontab',
            name='channel_id',
            field=models.CharField(help_text='Slack internal channel ID, will be automatically set based on channel_name', max_length=30),
        ),
        migrations.AlterField(
            model_name='crontab',
            name='gerrit_query',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]