from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Testing'

    def handle(self, *args, **kwargs):
        print('I ran...')
        self.stdout.write(self.style.SUCCESS('Ran successfully.'))

