# Altered Gemini's sample code for a test-generating file for an item.
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from tickets.models import Ticket
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'For Performance Testing. Generates requested number of Tickets as test data.  (Clears any existing Test Tickets first).'

    def add_arguments(self, parser):
        # You tell this command how many Tickets to make
        parser.add_argument('total', type=int,
                            help='Number of Tickets to Create')

    def handle(self, *args, **kwargs):
        total = kwargs['total']

        # 1.  Cleanup: Delete Tickets generated for testing....
        self.stdout.write(
            "Deleting existing auto-generated Test Tickets...")
        # ....To avoid a disaster, make sure to ONLY delete the tickets created for testing
        Ticket.objects.filter(summary__startswith="Test Ticket").delete()

        # 2. Prepare range of values to generate from
        roles = list(Group.objects.all())
        if not roles:
            self.stdout.write(self.style.ERROR(
                "No Groups found. Create some roles first!"))
            return

        authors = list(User.objects.all())

        if not authors:
            self.stdout.write(self.style.ERROR(
                "No users found in the database. Please create a superuser first!"
            ))
            return

        # Right now, generating all Tickets with Priority 'Low',
        # but may change later.
        # priorities = ['LOW', 'MEDIUM', 'HIGH']

        # 3. Generate the Tickets
        new_test_tickets = []
        lorem_ipsum_content = "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede mollis pretium. Integer tincidunt. Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus. Aenean leo ligula, porttitor eu, consequat vitae, eleifend ac, enim. Aliquam lorem ante, dapibus in, viverra quis, feugiat a, tellus. Phasellus viverra nulla ut metus varius laoreet. Quisque rutrum. Aenean imperdiet. Etiam ultricies nisi vel augue. Curabitur ullamcorper ultricies nisi. Nam eget dui. Etiam rhoncus. Maecenas tempus, tellus eget condimentum rhoncus, sem quam semper libero, sit amet adipiscing sem neque sed ipsum. Nam quam nunc, blandit vel, luctus pulvinar, hendrerit id, lorem. Maecenas nec odio et ante tincidunt tempus. Donec vitae sapien ut libero venenatis faucibus. Nullam quis ante. Etiam sit amet orci eget eros faucibus tincidunt. Duis leo. Sed fringilla mauris sit amet nibh. Donec sodales sagittis magna. Sed consequat, leo eget bibendum sodales, augue velit cursus nunc"

        for i in range(total):
            rand_num = random.randint(1, 12)
            full_content = lorem_ipsum_content * rand_num
            ticket = Ticket(summary=f"Test Ticket #{i}",  resolution_status='open', row_action='CREATE', author=random.choice(authors),  content=full_content, role=random.choice(
                roles), priority="LOW", tags="TEST_TICKET")

            new_test_tickets.append(ticket)

        Ticket.objects.bulk_create(new_test_tickets)
        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {total} test Tickets!"))
