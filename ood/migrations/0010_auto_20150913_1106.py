# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ood', '0009_minecraftserversettings_ip_address'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dropletstate',
            name='state',
        ),
        migrations.RemoveField(
            model_name='simpleserverstate',
            name='state',
        ),
        migrations.AddField(
            model_name='oodinstance',
            name='last_state_update',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='oodinstance',
            name='state',
            field=models.CharField(max_length=32, null=True),
        ),
    ]
