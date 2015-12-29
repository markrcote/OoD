# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ood', '0008_auto_20150913_1018'),
    ]

    operations = [
        migrations.AddField(
            model_name='minecraftserversettings',
            name='ip_address',
            field=models.GenericIPAddressField(null=True),
        ),
    ]
