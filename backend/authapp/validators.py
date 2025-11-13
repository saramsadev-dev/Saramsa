# In your serializers.py or validators.py
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_username_length(value):
    if len(value) < 3:
        raise ValidationError(
            _('Username must be at least 3 characters long.'),
            code='invalid_username_length'
        )

def validate_username_chars(value):
    import re
    if not re.match(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            _('Username can only contain letters, numbers, and @/./+/-/_ characters.'),
            code='invalid_username_chars'
        )