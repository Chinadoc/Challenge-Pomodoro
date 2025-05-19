"""
Internationalization (i18n) support for the Enhanced Pomodoro Timer.
Handles loading and managing translations for different languages.
"""

import gettext
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Callable, Any, Tuple

# Initialize logger
logger = logging.getLogger(__name__)

class Translator:
    """Handles translation of text strings for internationalization."""
    
    def __init__(self, domain: str = "pomodoro", 
                 localedir: Optional[Union[str, Path]] = None,
                 languages: Optional[List[str]] = None,
                 fallback: bool = True):
        """Initialize the translator.
        
        Args:
            domain: Translation domain (default: 'pomodoro')
            localedir: Directory containing translation files
            languages: List of language codes to try (in order of preference)
            fallback: Whether to fall back to the default language if translation fails
        """
        self.domain = domain
        self.localedir = Path(localedir) if localedir else None
        self.languages = languages or []
        self.fallback = fallback
        
        # Default to system language if no languages specified
        if not self.languages:
            self.languages = self._get_system_languages()
        
        # Initialize gettext
        self.translator: Optional[gettext.NullTranslations] = None
        self.current_language: str = ""
        
        # Load translations
        self._load_translations()
        
        # Dictionary of custom translations that override the gettext translations
        self._custom_translations: Dict[str, str] = {}
    
    def _get_system_languages(self) -> List[str]:
        """Get the system's preferred languages."""
        languages = []
        
        # Try to get language from environment variables
        for env_var in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
            lang = os.environ.get(env_var)
            if lang:
                # Handle language codes like 'en_US.UTF-8'
                lang = lang.split('.')[0].strip()
                if '_' in lang:
                    # Add both specific and generic language code (e.g., 'pt_BR' and 'pt')
                    generic_lang = lang.split('_')[0]
                    if generic_lang != lang and generic_lang not in languages:
                        languages.append(generic_lang)
                if lang not in languages:
                    languages.append(lang)
        
        # Fall back to English if no languages found
        if not languages:
            languages = ['en']
            
        return languages
    
    def _load_translations(self) -> None:
        """Load translations for the current language."""
        if not self.languages:
            self.translator = None
            self.current_language = ""
            return
        
        # Try each language in order of preference
        for lang in self.languages:
            try:
                # Try to load the translation
                trans = gettext.translation(
                    self.domain,
                    localedir=str(self.localedir) if self.localedir else None,
                    languages=[lang],
                    fallback=not self.fallback
                )
                
                # If we get here, the translation was loaded successfully
                self.translator = trans
                self.current_language = lang
                logger.info(f"Loaded translations for language: {lang}")
                return
                
            except FileNotFoundError:
                continue
            except Exception as e:
                logger.warning(f"Error loading translations for {lang}: {e}")
                continue
        
        # If we get here, no translations were found
        if self.fallback:
            self.translator = gettext.NullTranslations()
            self.current_language = self.languages[0] if self.languages else "en"
            logger.info(f"No translations found, using fallback ({self.current_language})")
        else:
            self.translator = None
            self.current_language = ""
            logger.warning("No translations found and fallback disabled")
    
    def gettext(self, message: str) -> str:
        """Translate a message.
        
        Args:
            message: The message to translate
            
        Returns:
            The translated message, or the original message if no translation is found
        """
        # Check for custom translation first
        if message in self._custom_translations:
            return self._custom_translations[message]
        
        # Use gettext translation if available
        if self.translator is not None:
            return self.translator.gettext(message)
        
        # Return the original message as a last resort
        return message
    
    # Alias for gettext
    gettext = lambda self, message: self.translator.gettext(message)
    
    # Define ngettext function
    def ngettext(self, singular: str, plural: str, n: int) -> str:
        """Translate a message with plural forms.
        
        Args:
            singular: The singular form of the message
            plural: The plural form of the message
            n: The number that determines the plural form
            
        Returns:
            The translated message, or the original message if no translation is found
        """
        # Check for custom translation first (not ideal for plurals, but included for completeness)
        key = f"{singular}\0{plural}\0{n}"
        if key in self._custom_translations:
            return self._custom_translations[key]
        
        # Use gettext translation if available
        if self.translator is not None:
            return self.translator.ngettext(singular, plural, n)
        
        # Return the appropriate form based on n
        return singular if n == 1 else plural
    
    def add_custom_translation(self, original: str, translation: str) -> None:
        """Add a custom translation that overrides the gettext translation.
        
        Args:
            original: The original text
            translation: The translated text
        """
        self._custom_translations[original] = translation
    
    def load_custom_translations(self, translations: Dict[str, str]) -> None:
        """Load multiple custom translations at once.
        
        Args:
            translations: Dictionary mapping original text to translated text
        """
        self._custom_translations.update(translations)
    
    def clear_custom_translations(self) -> None:
        """Clear all custom translations."""
        self._custom_translations.clear()
    
    def set_language(self, language: str) -> bool:
        """Set the current language.
        
        Args:
            language: Language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            bool: True if the language was set successfully
        """
        if language == self.current_language:
            return True
        
        # Store the current language at the beginning of the list
        old_languages = self.languages
        self.languages = [language] + [lang for lang in old_languages if lang != language]
        
        # Load translations for the new language
        try:
            self._load_translations()
            self.current_language = language
            return True
        except Exception as e:
            self.logger.error(f"Failed to set language to {language}: {e}")
            self.languages = old_languages
            return False
    
    def get_available_languages(self) -> List[Tuple[str, str]]:
        """Get a list of available languages.
        
        Returns:
            List of (code, name) tuples for available languages
        """
        # This method is not implemented in the original code
        pass

# Global translator instance
_translator: Optional[Translator] = None

def get_translator() -> Translator:
    """Get the global translator instance."""
    global _translator
    if _translator is None:
        # Initialize with default settings
        _translator = Translator()
    return _translator

def set_global_translator(translator: Translator) -> None:
    """Set the global translator instance.
    
    Args:
        translator: The translator instance to use globally
    """
    global _translator
    _translator = translator

def _(message: str) -> str:
    """Translate a message using the global translator.
    
    This is a convenience function that can be used as a shorthand for gettext().
    
    Args:
        message: The message to translate
        
    Returns:
        The translated message, or the original message if no translation is found
    """
    return get_translator().gettext(message)

def ngettext(singular: str, plural: str, n: int) -> str:
    """Translate a message with plural forms using the global translator.
    
    Args:
        singular: The singular form of the message
        plural: The plural form of the message
        n: The number that determines the plural form
        
    Returns:
        The translated message, or the appropriate form if no translation is found
    """
    return get_translator().ngettext(singular, plural, n)

def set_language(language: str) -> bool:
    """Set the current language for the global translator.
    
    Args:
        language: Language code (e.g., 'en', 'es', 'fr')
        
    Returns:
        bool: True if the language was set successfully
    """
    return get_translator().set_language(language)

def get_available_languages() -> List[Tuple[str, str]]:
    """Get a list of available languages.
    
    Returns:
        List of (code, name) tuples for available languages
    """
    return get_translator().get_available_languages()

def get_current_language() -> str:
    """Get the current language code.
    
    Returns:
        The current language code (e.g., 'en', 'es')
    """
    return get_translator().current_language
