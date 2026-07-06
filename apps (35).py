from rest_framework import serializers
from .models import Category, Product, ProductSize, Coupon


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent"]


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ["id", "size_label", "stock_quantity"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", default=None, read_only=True)
    sizes = ProductSizeSerializer(many=True, read_only=True)
    is_on_sale = serializers.BooleanField(read_only=True)
    primary_image = serializers.SerializerMethodField()
    secondary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "category_name", "gender",
            "age_min", "age_max", "price", "compare_at_price", "rating_avg",
            "rating_count", "is_on_sale", "is_featured", "primary_image",
            "secondary_image", "sizes", "stock_quantity",
        ]

    def get_primary_image(self, obj):
        if obj.primary_image:
            request = self.context.get("request")
            url = obj.primary_image.url
            return request.build_absolute_uri(url) if request else url
        return obj.primary_image_url or None

    def get_secondary_image(self, obj):
        if obj.secondary_image:
            request = self.context.get("request")
            url = obj.secondary_image.url
            return request.build_absolute_uri(url) if request else url
        return obj.secondary_image_url or self.get_primary_image(obj)


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField()
    order_subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
