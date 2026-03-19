from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from PIL import Image, UnidentifiedImageError
import io

# since we are using serializers, classes are best to use to create our views.
# and if we are not using methods, we have to replace decorators with rest_framework's views.
from rest_framework.views import APIView
from backend.model import classify_image
from .models import WasteItem
# import our serializer
from .serializers import WasteItemSerializer

#@api_view(['POST'])
#@parser_classes([MultiPartParser])
class WasteClassificationView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        if 'image' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['image']

        if not file.name:
            return Response({'error': 'Empty filename'}, status=status.HTTP_400_BAD_REQUEST)
#def classify(request):

        try:
            file.seek(0)
            img = Image.open(io.BytesIO(file.read()))
            img.load()
        except UnidentifiedImageError:
            return Response({'error': 'Cannot read image — unsupported or corrupted file'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Failed to open image: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = classify_image(img)

            suggestions_list = result.get('suggestions', [])
            suggestions_str = ", ".join([s['label'] for s in suggestions_list]) if suggestions_list else None

            file.seek(0)

            instance = WasteItem.objects.create(
                image=file,
                rule_key=result.get('label'),
                category=result.get('category'),
                waste_bin=result.get('bin',),
                confidence=result.get('confidence'),
                suggestions=suggestions_str,
                )

            return Response(WasteItemSerializer(instance).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Classification failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def health(request):
    return Response({'status': 'ok'})