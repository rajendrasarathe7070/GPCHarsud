from rest_framework import serializers
from .models import pyq , CheatSheet, Category


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
    
    
 
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class CheatSheetSerializer(serializers.ModelSerializer):
    owner_name    = serializers.ReadOnlyField(source="owner.username")
    category_name = serializers.ReadOnlyField(source="category.name")
    can_edit      = serializers.SerializerMethodField()
    file_url      = serializers.SerializerMethodField()
    pdf_view_url  = serializers.SerializerMethodField()

    class Meta:
        model  = CheatSheet
        fields = [
            "id", "title", "content", "category", "category_name",
            "owner", "owner_name", "is_public", "can_edit",
            "file", "file_url", "google_link", "pdf_view_url",
            "created_at", "updated_at",
        ]
        read_only_fields = ["owner", "created_at", "updated_at"]
        extra_kwargs = {
            "file": {"required": False, "allow_null": True},
            "google_link": {"required": False, "allow_null": True, "allow_blank": True},
        }

    def get_can_edit(self, obj):
        req = self.context.get("request")
        if not req or not req.user.is_authenticated:
            return False
        return req.user.is_staff or obj.owner_id == req.user.id

    def get_file_url(self, obj):
        if not obj.file:
            return None
        try:
            return obj.file.url
        except ValueError:
            return None

    def get_pdf_view_url(self, obj):
        return obj.pdf_view_url()

    def validate(self, attrs):
        # 🎯 kam se kam ek source
        file  = attrs.get("file",  getattr(self.instance, "file", None))
        glink = attrs.get("google_link", getattr(self.instance, "google_link", None))
        if not file and not glink:
            raise serializers.ValidationError(
                "File ya Google link me se ek zaroor do."
            )
        return attrs