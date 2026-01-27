from dataclasses import dataclass
from disnake import Locale


@dataclass
class Language:
    full_name: str
    short_code: str
    long_code: str


class Languages:
    german: Language = Language("Deutsch", "de", "de-DE")
    english: Language = Language("English", "en", "en-GB")
    spanish: Language = Language("Español", "es", "es-ES")
    french: Language = Language("Français", "fr", "fr-FR")
    italian: Language = Language("Italiano", "it", "it-IT")
    brazilian_portuguese: Language = Language("Português brasileiro", "pt-br", "pt-BR")
    russian: Language = Language("Pусский", "ru", "ru-RU")
    chinese: Language = Language("简化字", "zh-hans", "zh-Hans")
    all: list[Language] = [
        english,
        french,
        german,
        italian,
        brazilian_portuguese,
        russian,
        spanish,
        chinese,
    ]

    @staticmethod
    def get_from_locale(locale: Locale) -> Language:
        return LOCALES_DICT.get(locale, Languages.english)


LOCALES_DICT: dict[Locale, Language] = {
    Locale.fr: Languages.french,
    Locale.de: Languages.german,
    Locale.it: Languages.italian,
    Locale.pt_BR: Languages.brazilian_portuguese,
    Locale.ru: Languages.russian,
    Locale.es_ES: Languages.spanish,
    Locale.es_LATAM: Languages.spanish,
    Locale.zh_CN: Languages.chinese,
    Locale.zh_TW: Languages.chinese,
}
