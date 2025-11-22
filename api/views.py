from django.core.cache import cache
import hashlib
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

from .serializers import (
    AbuseAnalysisSerializer, AnalysisResponseSerializer
)

from .utils.ai_detector import AbuseDetector
from .utils.text_processor import TextProcessor

def generate_cache_key(content, content_type='text'):
    """
    Generate a unique cache key based on content and type
    """
    content_hash = hashlib.md5(content.encode() if isinstance(content, str) else content).hexdigest()
    return f"safeguard_{content_type}_{content_hash}"

@api_view(['POST'])
def analyze_text(request):
    serializer = AbuseAnalysisSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    text = serializer.validated_data.get('text')
    language = serializer.validated_data.get("language", "en")
    
    # Generate cache key
    cache_key = generate_cache_key(text, 'text')
    
    # Check cache first
    cached_result = cache.get(cache_key)
    
    if cached_result:
        print(f"Cache HIT for text analysis: {cache_key}")
        response_serializer = AnalysisResponseSerializer(cached_result)
        return Response(response_serializer.data)
    
    print(f"Cache MISS for text analysis: {cache_key}")
    
    detector = AbuseDetector()
    analysis_result = detector.analyze_text(text)
    cache.set(cache_key, analysis_result, settings.CACHE_TIMEOUT)
    
    response_serializer = AnalysisResponseSerializer(analysis_result)
    return Response(response_serializer.data)

@api_view(['POST'])
def analyze_image(request):
    """Analyze image content directly using Gemini Vision"""
    if 'image' not in request.FILES:
        return Response(
            {'error': 'No image file provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    
    image_file = request.FILES['image']
    
    # Validate image file
    if not image_file.content_type.startswith('image/'):
        return Response(
            {'error': 'File must be an image'},
            status=status.HTTP_400_BAD_REQUEST
        )
    # Read image content for cache key
    image_content = image_file.read()
    image_file.seek(0)  # Reset file pointer for processing
    
    # Generate cache key from image content
    cache_key = generate_cache_key(image_content, 'image')
    
    # Check cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        print(f"Cache HIT for image analysis: {cache_key}")
        response_serializer = AnalysisResponseSerializer(cached_result)
        return Response(response_serializer.data)
    
    print(f"Cache MISS for image analysis: {cache_key}")    
    
    # Analyze image directly using AI vision
    detector = AbuseDetector()
    analysis_result = detector.analyze_image(image_file)
    
    cache.set(cache_key, analysis_result, settings.CACHE_TIMEOUT)
    
    response_serializer = AnalysisResponseSerializer(analysis_result)
    return Response(response_serializer.data)

@api_view(["GET"])

def support_resources(request):
    
    country = request.GET.get("country", "KE")
    
    resources = {
            "KE": [
                {
                "name": "Gender Violence Recovery Centre",
                "phone": "+254-703-034-000",
                "website": "https://gvrc.or.ke/",
                "description": "Medical and psychological support for GBV survivors.",
                "category": "medical"
                },
                {
                "name": "FIDA Kenya",
                "phone": "+254-20-2711535",
                "website": "https://fidakenya.org",
                "description": "Legal aid and support for women.",
                "category": "legal"
                },
                {
                "name": "Childline Kenya",
                "phone": "116",
                "website": "https://childlinekenya.co.ke",
                "description": "National helpline for children affected by violence and abuse.",
                "category": "emergency"
                },
                {
                "name": "CREAW Kenya",
                "phone": "+254-722-822-998",
                "website": "https://creawkenya.org",
                "description": "Rights-based organization supporting survivors of GBV.",
                "category": "support"
                }
            ],

            "NG": [
                {
                "name": "Women at Risk International Foundation (WARIF)",
                "phone": "+234-803-334-5566",
                "website": "https://warifng.org",
                "description": "GBV prevention, rape crisis, and response services.",
                "category": "support"
                },
                {
                "name": "Mirabel Centre",
                "phone": "+234-815-584-0000",
                "website": "https://mirabelcentre.org",
                "description": "Sexual assault referral centre providing free medical & counseling services.",
                "category": "medical"
                },
                {
                "name": "National GBV Hotline (Nigeria)",
                "phone": "0800 033 33 33",
                "website": "",
                "description": "24/7 national helpline for reporting GBV cases.",
                "category": "emergency"
                }
            ],

            "ZA": [
                {
                "name": "GBV Command Centre",
                "phone": "0800 428 428",
                "website": "",
                "description": "24/7 emergency support and counseling for GBV survivors.",
                "category": "emergency"
                },
                {
                "name": "TEARS Foundation South Africa",
                "phone": "+27-10-590-5920",
                "website": "https://tears.co.za",
                "description": "Support for survivors of rape and sexual abuse.",
                "category": "support"
                },
                {
                "name": "People Opposing Women Abuse (POWA)",
                "phone": "+27-11-642-4345",
                "website": "https://powa.co.za",
                "description": "Shelter, legal, and counseling services for abused women.",
                "category": "legal"
                }
            ],

            "UG": [
                {
                "name": "Uganda Child Helpline",
                "phone": "116",
                "website": "https://mglsd.go.ug",
                "description": "National toll-free helpline for child and women protection.",
                "category": "emergency"
                },
                {
                "name": "Uganda Women’s Network (UWONET)",
                "phone": "+256-414-286-063",
                "website": "https://uwonet.or.ug",
                "description": "Advocacy and support services for women survivors.",
                "category": "support"
                }
            ],

            "TZ": [
                {
                "name": "Tanzania National GBV Helpline",
                "phone": "116",
                "website": "",
                "description": "Child and gender-based violence hotline.",
                "category": "emergency"
                },
                {
                "name": "Tanzania Gender Networking Programme",
                "phone": "+255-22-266-4051",
                "website": "https://tgnp.or.tz",
                "description": "Support and advocacy for women and girls experiencing violence.",
                "category": "support"
                }
            ],

            "GH": [
                {
                "name": "Ghana Domestic Violence & Victim Support Unit (DOVVSU)",
                "phone": "+233-302-777-395",
                "website": "",
                "description": "Police-led support for victims of domestic and sexual violence.",
                "category": "emergency"
                },
                {
                "name": "ARK Foundation Ghana",
                "phone": "+233-302-911-385",
                "website": "https://arkfoundationghana.org",
                "description": "Shelter, legal, and counseling services for survivors.",
                "category": "support"
                }
            ],

            "RW": [
                {
                "name": "Isange One Stop Center",
                "phone": "116",
                "website": "https://npprwanda.gov.rw",
                "description": "Free medical, legal, and psychosocial support to GBV victims.",
                "category": "medical"
                }
            ],

            "ET": [
                {
                "name": "Ethiopian Women Lawyers Association",
                "phone": "+251-11-467-1750",
                "website": "https://ewlaethiopia.org",
                "description": "Legal assistance and advocacy for women survivors.",
                "category": "legal"
                },
                {
                "name": "Addis Ababa Women’s Shelter",
                "phone": "+251-11-552-5995",
                "website": "",
                "description": "Shelter and support services for abused women.",
                "category": "support"
                }
            ],

            "ZM": [
                {
                "name": "Yamala Crisis Line Zambia",
                "phone": "116",
                "website": "",
                "description": "GBV hotline for women, girls, and children.",
                "category": "emergency"
                },
                {
                "name": "Women and Law in Southern Africa (WLSA Zambia)",
                "phone": "+260-211-255-539",
                "website": "https://wlsazambia.org",
                "description": "Legal services and protection programs for women survivors.",
                "category": "legal"
                }
            ],

            "ZW": [
                {
                "name": "Musasa Project",
                "phone": "+263-24-279-303/4",
                "website": "https://musasa.co.zw",
                "description": "Counseling, shelters, and protection services for GBV survivors.",
                "category": "support"
                },
                {
                "name": "Zimbabwe National GBV Hotline",
                "phone": "0808 00 33 333",
                "website": "",
                "description": "24/7 hotline for victims of gender-based violence.",
                "category": "emergency"
                }
            ]
            }

    


    country_resources = resources.get(country, resources['KE'])
    return Response(country_resources)

@api_view(['GET'])
def safety_tips(request):
    """Get digital safety tips"""
    tips = {
        'general': [
            'Never share passwords or personal information online',
            'Use two-factor authentication on all accounts',
            'Be cautious about what you share on social media',
            'Regularly check your privacy settings',
            'Keep software and apps updated'
        ],
        'harassment': [
            'Document all abusive messages with screenshots',
            'Block the harasser immediately',
            'Report to the platform and local authorities',
            'Reach out to trusted friends or family',
            'Contact support organizations for help'
        ],
        'emergency': [
            'If in immediate danger, contact local emergency services',
            'Save evidence of threats for legal purposes',
            'Inform trusted contacts about your situation',
            'Consider changing your online routines and accounts'
        ]
    }
    
    return Response(tips)

@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'service': 'SafeguardAI Backend',
        'version': '1.0.0'
    })