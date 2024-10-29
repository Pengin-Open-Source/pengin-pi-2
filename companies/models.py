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
    # For now, setting these fields to null if the user is deleted.
    # (Once could argue that if staff want to DELETE a user
    # rather than setting the user to be inactive, they are ready to
    # erase the users from the database completely.  However,
    # if that's the case, the DBA will have to be notified to
    # "scrub" any records in history from any info related to the user
    # who created this company)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='companies_created', null=True)
    last_edited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,   null=True)
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
                # Check to see if the last_edited_by or created_by fields are null.
                # That can happen when the editing or creating user has been deleted from the system
                if original_company.last_edited_by:
                    last_editor = original_company.last_edited_by.pk
                else:
                    last_editor = None
                if original_company.created_by:
                    company_creator = original_company.created_by.pk
                else:
                    company_creator = None
                # Prior change was editing of the Company
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
                                                created_by=company_creator,
                                                last_edited_by=last_editor,
                                                row_action=original_company.row_action)

                company_backup.save()

            super().save(*args, **kwargs)

            # if this is a pre-delete save,  the Company row will have been updated to contain
            # 1) The action/method: "DELETE"
            # 2) The User who Deleted the Company
            # 3) The time of the deletion
            # We need to make sure this information is copied into CompanyHistory
            # before we delete the Company
            # (If CompanyHistory needs to be totally deleted, that should be done
            # by a DBA)
            if save_method == 'DELETE':
                archived_company = CompanyHistory(company_id=self.id,
                                                  name=self.name,
                                                  phone=self.phone,
                                                  city=self.city,
                                                  state=self.state,
                                                  country=self.country,
                                                  zipcode=self.zipcode,
                                                  email=self.email,
                                                  address1=self.address1,
                                                  address2=self.address2,
                                                  date=self.date,
                                                  created_by=company_creator,
                                                  last_edited_by=last_editor,
                                                  row_action=self.row_action)
                archived_company.save()


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
    created_by = models.UUIDField(db_index=True, null=True)
    last_edited_by = models.UUIDField(db_index=True, null=True)
    row_action = models.CharField(max_length=10, default='ERROR')


class CompanyMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='members', null=True, blank=True)
    user = models.ForeignKey(
        # Allow null for user
        User, on_delete=models.CASCADE, related_name='company_memberships', null=True)
    date = models.DateTimeField(default=timezone.now)
    # Setting to null on delete for now....
    # Allowing null for default in case
    added_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='members_added',  null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL,  null=True)
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.user.name + ", " + self.company.name)

    def save(self, *args, **kwargs):
        save_method = self.row_action
        with transaction.atomic():
            # Do backup of current values in the row first.
            # (Note we backup before a DELETE.  Frequently,  a
            # row will have no backup history until we enter DELETE)
            # , Also Rows will still be backed up even if 'ERROR' was assigned to the row_action.
            if save_method != "CREATE":
                company_member_current = CompanyMember.objects.get(pk=self.pk)

                # Check to see if the last_edited_by or created_by fields are null.
                # That can happen when the editing or creating user has been deleted from the system
                if company_member_current.last_edited_by:
                    deletor = company_member_current.deleted_by.pk
                else:
                    deletor = None
                if company_member_current.added_by:
                    member_adder = company_member_current.added_by.pk
                else:
                    member_adder = None

                company_member_backup = CompanyMemberHistory(company_member_id=company_member_current.id,
                                                             company=company_member_current.company.pk,
                                                             user=company_member_current.user.pk,
                                                             date=company_member_current.date,
                                                             added_by=member_adder,
                                                             deleted_by=deletor,
                                                             row_action=company_member_current.row_action)

                company_member_backup.save()

            super().save(*args, **kwargs)

            # if this is a pre-delete save,  the CompanyMember row will have been updated to contain
            # 1) The action/method: "DELETE"
            # 2) The User who Deleted the Member
            # 3) The time of the deletion
            # We need to make sure this information is copied into CompanyMemberHistory
            # before we delete the CompanyMember
            # (If CompanyMemberHistory needs to be totally deleted, that should be done
            # by a DBA)
            if save_method == 'DELETE':
                archived_member = CompanyMemberHistory(company_member_id=self.id,
                                                       company=self.company.pk,
                                                       # this value should always be here.
                                                       # user associated with member does not get set null,  it will CASCADE DELETE the company member
                                                       # - and CASCADE deletes don't trigger this
                                                       # So best practice is to delete the CompanyMembers first before deleting its User -
                                                       # - unless of course staff intends to wipe out all history associated with the user,
                                                       # Which they might.
                                                       user=self.user.pk,
                                                       date=self.date,
                                                       added_by=member_adder,
                                                       deleted_by=deletor,
                                                       row_action=self.row_action)
                archived_member.save()


class CompanyMemberHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_member_id = models.UUIDField(db_index=True)
    company = models.UUIDField(db_index=True, null=True)
    user = models.UUIDField(db_index=True, null=True)
    date = models.DateTimeField(default=timezone.now)
    added_by = models.UUIDField(db_index=True, null=True)
    deleted_by = models.UUIDField(db_index=True, null=True)
    row_action = models.CharField(max_length=10, default='ERROR')
