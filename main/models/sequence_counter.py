from django.db import models, transaction
import uuid

# Worked with Gemini to get a multi-object
# table for sequencing different objects.
# This is NOT for the UUIDs - this are
# for anything that needs a human-readable
# numeric id, in addition to its UUID.
# We use this table to get the next such id.
# So for example, a Ticket will have a UUID,
# but be seen by the user as Ticket #134.
# By default,  each row in the database /
# counter for a given kind of object,  starts
# with 0, meaning the first object created will 
# be  given the next number, 1.
# However,  if there is a migration
# of existing items into the system, a script
# or DBA may set the item Counter to whatever 
# number is the highest id being used.


class SequenceCounter(models.Model):
    # tickets,  forum posts, or whatever needs a human-friendly id.
    counted_item = models.CharField(max_length=100, primary_key=True)
    highest_used_numeric_id = models.PositiveIntegerField(default=0)

    @classmethod
    def get_next_id(cls, counting_this):
        with transaction.atomic():
            # Lock the specific row for 'ticket', 'group', etc.
            counter, created = cls.objects.select_for_update().get_or_create(
                counted_item=counting_this
            )
            counter.highest_used_numeric_id += 1
            counter.save()
            return counter.highest_used_numeric_id
