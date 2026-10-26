from rest_framework import serializers
from .models import pyq

class PYQSerializer(serializers.ModelSerializer):
    class Meta:
        model = pyq
        fields = "__all__"

    def validate_pdf_file(self, value):
        if value:
            if not value.name.lower().endswith(".pdf"):
                raise serializers.ValidationError("Sirf PDF file allowed hai.")
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("File 10MB se choti honi chahiye.")
        return value