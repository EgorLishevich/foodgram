import csv

from django.core.management.base import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.import_tags()
        print('Загрузка тегов для базы данных завершена.')

    def import_tags(self, file='tags.csv'):
        path = f'./data/{file}'
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                status, created = Tag.objects.update_or_create(
                    name=row[0],
                    slug=row[1]
                )
