from rest_framework import serializers
from session.models import Session, SessionStatus



class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = "__all__"


class StartSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ["id", "name", "description", "started_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else None
        validated_data["owner"] = user
        return super().create(validated_data)


class ResumeSessionSerializer(serializers.Serializer):
    id = serializers.UUIDField()

    def validate_id(self, value):
        try:
            session = Session.objects.get(id=value,  status=SessionStatus.STOPPED)
        except Session.DoesNotExist:
            raise serializers.ValidationError("Active session with this ID does not exist.")
        return value


class StopSessionSerializer(serializers.Serializer):
    id = serializers.UUIDField()

    def validate_id(self, value):
        try:
            session = Session.objects.get(id=value, status=SessionStatus.RUNNING)
        except Session.DoesNotExist:
            raise serializers.ValidationError("Active session with this ID does not exist.")
        return value
