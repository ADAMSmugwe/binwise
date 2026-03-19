from rest_framework import serializers
from .models import WasteItem

class WasteItemSerializer(serializers.ModelSerializer):
    category = serializers.CharField(read_only=True)
    waste_bin = serializers.CharField(read_only=True)
    confidence = serializers.FloatField(read_only=True)

    item_name = serializers.ReadOnlyField()
    explanation = serializers.ReadOnlyField()

    class Meta:
        model = WasteItem
        fields = [
            'id',
            'image',
            'item_name',
            'waste_bin',
            'category',
            'confidence',
            'explanation',
            'suggestions',
            'created_at'
        ]