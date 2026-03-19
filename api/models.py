from django.db import models
import os
from backend import waste_rules as wr

# Create your models here.

# so we have the category, confidence, bin and when it was created.
class WasteItem(models.Model):
    CATEGORY_CHOICES = [
        ('recyclable', 'Recyclable'),
        ('organic', 'Organic'),
        ('hazardous', 'Hazardous'),
        ('unclear', 'Unclear'),
        ('multiple_items', 'Multiple Items'),

    ]

    BIN_CHOICES = [
        ('black', 'Black'),
        ('green', 'Green'),
        ('blue', 'Blue'),
        ('specialist', 'Specialist'),
        ('gray', 'Gray'),
        ('multiple', 'Multiple'),
    ]

    image = models.ImageField('waste_uploads')

    rule_key = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='unclear')
    waste_bin = models.CharField(max_length=20, choices=BIN_CHOICES, default='gray')
    confidence = models.FloatField(default=0.0)
    suggestions = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def item_name(self):
        if self.rule_key:
            return self.rule_key

    @property
    def explanation(self):
        if self.category == 'multiple_items' or self.rule_key == 'mixed waste':
            return "It looks like there are multiple waste items in this photo. Please photograph one item at a time for an accurate result."

        # Unclear / low confidence
        if self.category == 'unclear':
            if self.suggestions:
                return f"Not confident enough. Most likely matches: {self.suggestions}"
            return "Not confident enough to classify this item."

        # Normal classification — look up explanation from rules
        if self.rule_key in wr.RULES:
            return wr.RULES[self.rule_key].get('explanation', 'No explanation available.')

        return "No explanation available."

    def __str__(self):
        return f"{self.item_name} ({self.get_category_display()})"

    def filename(self):
        return os.path.basename(self.image.name)