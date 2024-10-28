from django.db import models, transaction
from main.models.users import User
from django.utils import timezone
import uuid


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    zipcode = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    address1 = models.CharField(max_length=50)
    address2 = models.CharField(max_length=50, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    # Setting to null on delete for now.
    # (Once could argue that if admins want to DELETE a user
    # rather than setting them to be inactive, they are ready to
    # erase the users from the database completely.  However,
    # if that's the case, the DBA will have to be noticed to
    # delete or "scrub" any records in history related to the user
    # who created this company)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='companies')
    last_edited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,  null=True)
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        save_method = self.row_action
        # all backups must complete properly for changes to be saved
        with transaction.atomic():
            # Do backup of current values in the row first.
            # (Note we backup before a DELETE.  Frequently,  a
            # row will have no backup history until we enter DELETE)
            # , Also Rows will still be backed up even if 'ERROR' was assigned to the row_action.
            if save_method != "CREATE":
                original_company = Company.objects.get(pk=self.pk)
                # Prior change was editing of the Company
                if original_company.last_edited_by:
                    company_backup = CompanyHistory(company_id=original_company.id,
                                                    name=original_company.name,
                                                    phone=original_company.phone,
                                                    city=original_company.city,
                                                    state=original_company.state,
                                                    country=original_company.country,
                                                    zipcode=original_company.zipcode,
                                                    email=original_company.email,
                                                    address1=original_company.address1,
                                                    address2=original_company.address2,
                                                    date=original_company.date,
                                                    created_by=original_company.created_by.pk,
                                                    last_edited_by=original_company.last_edited_by.pk,
                                                    row_action=original_company.row_action)
                else:  # Prior change was Creation of the company. No last_edited_by
                    company_backup = CompanyHistory(company_id=original_company.id,
                                                    name=original_company.name,
                                                    phone=original_company.phone,
                                                    city=original_company.city,
                                                    state=original_company.state,
                                                    country=original_company.country,
                                                    zipcode=original_company.zipcode,
                                                    email=original_company.email,
                                                    address1=original_company.address1,
                                                    address2=original_company.address2,
                                                    date=original_company.date,
                                                    created_by=original_company.created_by.pk,
                                                    row_action=original_company.row_action)

                company_backup.save()

            super().save(*args, **kwargs)


class CompanyHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    zipcode = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    address1 = models.CharField(max_length=50)
    address2 = models.CharField(max_length=50, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    created_by = models.UUIDField(db_index=True)
    last_edited_by = models.UUIDField(db_index=True, null=True)
    row_action = models.CharField(max_length=10, default='ERROR')


class CompanyMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='members', null=True, blank=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True)  # Allow null for user
    date = models.DateTimeField(default=timezone.now)
    # Setting to null on delete for now....
    # Allowing null for default in case
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL)
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.user.name + ", " + self.company.name)


class CompanyMemberHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_member_id = models.UUIDField(db_index=True)
    company = models.UUIDField(db_index=True, null=True)
    user = models.UUIDField(db_index=True, null=True)
    date = models.DateTimeField(default=timezone.now)
    added_by = models.UUIDField(db_index=True)
    deleted_by = models.UUIDField(db_index=True, null=True)
    row_action = models.CharField(max_length=10, default='ERROR')

    def save(self, *args, **kwargs):
        save_method = self.row_action
        with transaction.atomic():
            # Do backup of current values in the row first.
            # (Note we backup before a DELETE.  Frequently,  a
            # row will have no backup history until we enter DELETE)
            # , Also Rows will still be backed up even if 'ERROR' was assigned to the row_action.
            if save_method != "CREATE":
                company_member_current = CompanyMember.objects.get(pk=self.pk)

                # View's code called a save preparing for a delete, before this call.
                if company_member_current.deleted_by:
                    company_member_backup = CompanyMemberHistory(company_member_id=company_member_current.id,
                                                                 company=company_member_current.company.pk,
                                                                 user=company_member_current.user.pk,
                                                                 date=company_member_current.date,
                                                                 added_by=company_member_current.created_by.pk,
                                                                 deleted_by=company_member_current.last_edited_by.pk,
                                                                 row_action=company_member_current.row_action)
                else:  # Prior change was Creation of the CompanyMember
                    company_member_backup = CompanyHistory(company_member_id=company_member_current.id,
                                                           company=company_member_current.company.pk,
                                                           user=company_member_current.user.pk,
                                                           date=company_member_current.date,
                                                           added_by=company_member_current.created_by.pk,
                                                           row_action=company_member_current.row_action)

                company_member_backup.save()
