# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0002_add_itemtype'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='abandoned',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
