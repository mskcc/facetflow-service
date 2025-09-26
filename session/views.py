from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Session
from .session_manager import start_session, stop_session

from .serializers import StartSessionSerializer, StopSessionSerializer, ResumeSessionSerializer, SessionSerializer


class StartSessionView(APIView):
    serializer_class = StartSessionSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if serializer.is_valid():
            session = serializer.save()
            start_session(str(session.id))
            return Response(StartSessionSerializer(session).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResumeSessionView(APIView):
    serializer_class = ResumeSessionSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResumeSessionSerializer(data=request.data)
        if serializer.is_valid():
            session = Session.objects.get(id=serializer.validated_data["id"])
            start_session(str(session.id))
            return Response(StartSessionSerializer(session).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StopSessionView(APIView):
    serializer_class = StopSessionSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StopSessionSerializer(data=request.data)
        if serializer.is_valid():
            session = Session.objects.get(id=serializer.validated_data["id"])
            stop_session(str(session.id))
            return Response({"message": f"Session {session.id} stopped."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        sessions = Session.objects.filter(owner=user).all()
        return Response(SessionSerializer(sessions, many=True).data, status=status.HTTP_200_OK)