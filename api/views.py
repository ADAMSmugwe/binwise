from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from PIL import Image, UnidentifiedImageError
import io

from backend.model import classify_image
from .models import WasteItem


@api_view(['POST'])
@parser_classes([MultiPartParser])
def classify(request):
    if 'image' not in request.FILES:
        return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['image']

    if file.name == '':
        return Response({'error': 'Empty filename'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        img = Image.open(io.BytesIO(file.read()))
    except UnidentifiedImageError:
        return Response({'error': 'Cannot read image — unsupported or corrupted file'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'Failed to open image: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = classify_image(img)
    except Exception as e:
        return Response({'error': f'Classification failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if result.get('category') not in ('multiple_items', 'unclear'):
        file.seek(0)
        WasteItem.objects.create(
            image=file,
            rule_key=result.get('label', ''),
            category=result.get('category', 'unclear'),
            waste_bin=result.get('bin', 'gray'),
            confidence=result.get('confidence', 0.0),
        )

    return Response(result, status=status.HTTP_200_OK)


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok'})
