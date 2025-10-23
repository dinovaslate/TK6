from django.db import migrations


def create_initial_data(apps, schema_editor):
    Category = apps.get_model('main', 'Category')
    Venue = apps.get_model('main', 'Venue')
    AddOn = apps.get_model('main', 'AddOn')

    categories = {
        'Futsal': Category.objects.create(name='Futsal'),
        'Badminton': Category.objects.create(name='Badminton'),
        'Basketball': Category.objects.create(name='Basketball'),
    }

    venues_data = [
        {
            'name': 'Arena Nusantara Futsal',
            'city': 'Jakarta',
            'category': categories['Futsal'],
            'price_per_hour': 250000,
            'description': 'Premium synthetic turf with climate control and pro-grade lighting.',
            'facilities': 'Locker room, shower, scoreboard, cafe corner',
            'image_url': 'https://images.unsplash.com/photo-1521412644187-c49fa049e84d?auto=format&fit=crop&w=800&q=80',
            'address': 'Jl. Merdeka No. 8, Jakarta Pusat',
            'addons': [
                ('Match Official', 150000),
                ('Team Jersey Rental', 200000),
            ],
        },
        {
            'name': 'Yogyakarta Smash Court',
            'city': 'Yogyakarta',
            'category': categories['Badminton'],
            'price_per_hour': 120000,
            'description': 'Tournament-ready badminton courts with professional flooring.',
            'facilities': 'Air conditioned hall, stringing service, pro shop',
            'image_url': 'https://images.unsplash.com/photo-1521412644187-c49fa049e84d?auto=format&fit=crop&w=800&q=80',
            'address': 'Jl. Malioboro No. 12, Yogyakarta',
            'addons': [
                ('Racket Stringing', 80000),
                ('Coaching Session', 180000),
            ],
        },
        {
            'name': 'Bandung Hoop Center',
            'city': 'Bandung',
            'category': categories['Basketball'],
            'price_per_hour': 300000,
            'description': 'Indoor basketball arena with wooden flooring and digital scoreboard.',
            'facilities': 'Locker room, physiotherapy room, cafe',
            'image_url': 'https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=800&q=80',
            'address': 'Jl. Braga No. 22, Bandung',
            'addons': [
                ('Scorekeeper', 100000),
                ('Video Highlights', 220000),
            ],
        },
    ]

    for data in venues_data:
        addons = data.pop('addons')
        venue = Venue.objects.create(**data)
        for name, price in addons:
            AddOn.objects.create(venue=venue, name=name, price=price)


def remove_initial_data(apps, schema_editor):
    Category = apps.get_model('main', 'Category')
    Category.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_data, reverse_code=remove_initial_data),
    ]
