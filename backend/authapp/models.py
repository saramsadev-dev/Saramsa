# Django models are no longer needed since we're using Cosmos DB only
# from django.db import models
# from django.contrib.auth.models import User

# class UserProfile(models.Model):
#     ROLE_CHOICES = (
#         ('admin', 'Admin'),
#         ('user', 'User'),
#         ('restricted user', 'Restricted User'),
#     )
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
#     role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

#     def __str__(self):
#         return f"{self.user.username} - {self.role}"

# Note: User data is now stored in Cosmos DB users container
# with the following structure:
# {
#   "id": "user_uuid",
#   "type": "user",
#   "username": "username",
#   "email": "email@example.com",
#   "password": "hashed_password",
#   "first_name": "First",
#   "last_name": "Last",
#   "is_active": true,
#   "is_staff": false,
#   "date_joined": "2024-01-01T00:00:00Z",
#   "profile": {
#     "role": "user"
#   }
# }