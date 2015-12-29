# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ood', '0010_auto_20150913_1106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dropletstate',
            name='ood',
            field=models.OneToOneField(to='ood.OodInstance'),
        ),
        migrations.AlterField(
            model_name='minecraftserversettings',
            name='ood',
            field=models.OneToOneField(to='ood.OodInstance'),
        ),
        migrations.AlterField(
            model_name='serverplayerstate',
            name='ood',
            field=models.OneToOneField(to='ood.OodInstance'),
        ),
        migrations.AlterField(
            model_name='simpleserverstate',
            name='ood',
            field=models.OneToOneField(to='ood.OodInstance'),
        ),
    ]
