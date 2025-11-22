from rest_framework import serializers

class AbuseAnalysisSerializer(serializers.Serializer):
    text = serializers.CharField(required=True)
    language = serializers.CharField(default='en')
    
class AnalysisResponseSerializer(serializers.Serializer):
    risk_level = serializers.CharField()
    category = serializers.CharField()
    confidence = serializers.IntegerField()
    explanation = serializers.CharField()
    immediate_actions = serializers.ListField(child=serializers.CharField())
    detected_text = serializers.CharField(required=False, allow_blank=True) 
       