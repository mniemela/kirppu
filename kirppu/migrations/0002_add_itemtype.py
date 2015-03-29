# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('kirppu', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UIText',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(help_text='Identifier of the textitem', unique=True, max_length=16, blank=True)),
                ('text', models.CharField(help_text='Textitem in UI', max_length=16384)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='clerk',
            options={'permissions': (('oversee', 'Can perform overseer actions'),)},
        ),
        migrations.AddField(
            model_name='item',
            name='adult',
            field=models.CharField(default=b'no', max_length=8, choices=[(b'yes', 'Item allowed only to adult shoppers, contains porn etc.'), (b'no', 'Item allowed to all shoppers')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='item',
            name='itemtype',
            field=models.CharField(default=b'other', max_length=24, choices=[(b'manga-finnish', 'Finnish manga book'), (b'manga-english', 'English manga book'), (b'manga-other', 'Manga book in another language'), (b'book', 'Non-manga book'), (b'magazine', 'Magazine'), (b'movie-tv', 'Movie or TV-series'), (b'game', 'Game'), (b'figurine-plushie', 'Figurine or a stuffed toy'), (b'clothing', 'Clothing'), (b'other', 'Other item')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='clerk',
            name='access_key',
            field=models.CharField(null=True, validators=[django.core.validators.RegexValidator(b'^[0-9a-fA-F]{14}$', message=b'Must be 14 hex chars.')], max_length=128, blank=True, help_text='Access code assigned to the clerk. 14 hexlets.', unique=True, verbose_name='Access key value'),
            preserve_default=True,
        ),
    ]
