# Generated by Django 3.2.5 on 2021-10-03 23:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_perfilinversor'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilinversor',
            name='descripcion',
            field=models.CharField(blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='perfilinversor',
            name='perfil',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
