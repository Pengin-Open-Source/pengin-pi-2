from django.db import models
from django.conf import settings
from forums.models import ForumComment, ForumPost, Thread, Thread, Role

# Add author relationship to ForumComment model
ForumComment.add_to_class('author', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments'))

# Add author relationship to ForumPost model
ForumPost.add_to_class('author', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts'))

# Add users relationship to Thread model
Thread.add_to_class('users', models.ManyToManyField(settings.AUTH_USER_MODEL, through='relations.UserThreadRole', related_name='threads'))


'''
class UserThreadRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.email} - {self.thread.name} - {self.role.name}'
'''