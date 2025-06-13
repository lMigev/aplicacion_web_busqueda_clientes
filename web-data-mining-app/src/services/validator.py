from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import carrier, geocoder
import re

class DataValidator:
    @staticmethod
    def validate_email(email):
        """Valida si un email es válido"""
        if not email:
            return False, "Email vacío"
        
        try:
            validated_email = validate_email(email)
            return True, validated_email.email
        except EmailNotValidError as e:
            return False, str(e)
    
    @staticmethod
    def validate_phone(phone, region="PA"):
        """Valida si un teléfono es válido (específico para Panamá)"""
        if not phone:
            return False, "Teléfono vacío"
        
        try:
            # Limpiar el número de caracteres especiales
            cleaned_phone = re.sub(r'[^\d+]', '', phone)
            
            # Parsear el número
            parsed_number = phonenumbers.parse(cleaned_phone, region)
            
            # Verificar si es válido
            if phonenumbers.is_valid_number(parsed_number):
                # Formatear el número
                formatted = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                return True, formatted
            else:
                return False, "Número de teléfono inválido"
                
        except phonenumbers.NumberParseException as e:
            return False, f"Error al parsear el teléfono: {e}"
    
    @staticmethod
    def calculate_quality_score(contact_data):
        """Calcula una puntuación de calidad para el contacto (0-100)"""
        score = 0
        
        # Nombre (20 puntos)
        if contact_data.get('name') and len(contact_data['name']) > 5:
            score += 20
        
        # Email válido (25 puntos)
        if contact_data.get('email_valid'):
            score += 25
        
        # Teléfono válido (25 puntos)  
        if contact_data.get('phone_valid'):
            score += 25
        
        # Ubicación (15 puntos)
        if contact_data.get('location'):
            score += 15
        
        # Website válido (15 puntos)
        if contact_data.get('website') and contact_data['website'].startswith('http'):
            score += 15
        
        return min(score, 100)  # Máximo 100
    
    @staticmethod
    def is_duplicate(new_contact, existing_contacts):
        """Detecta si un contacto es duplicado"""
        for existing in existing_contacts:
            # Duplicado por email
            if (new_contact.get('email') and existing.email and 
                new_contact['email'].lower() == existing.email.lower()):
                return True, f"Email duplicado: {existing.email}"
            
            # Duplicado por teléfono
            if (new_contact.get('phone') and existing.phone and
                new_contact['phone'] == existing.phone):
                return True, f"Teléfono duplicado: {existing.phone}"
            
            # Duplicado por website
            if (new_contact.get('website') and existing.website and
                new_contact['website'] == existing.website):
                return True, f"Website duplicado: {existing.website}"
        
        return False, None
