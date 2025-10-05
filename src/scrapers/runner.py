from .finquesmarques_sql import FinquesmarquesScraper
from .nouaire_sql import NouaireScraper
from .expofinques_sql import ExpofinquesScraper
from .claus_sql import ClausScraper
from .pisosad_sql import PisosAdScraper
from .pisoscom_sql import PisoscomScraper

def run_all_scrapers():
    """
    Ejecuta todos los scrapers disponibles
    """
    scrapers = [
        FinquesmarquesScraper(),
        NouaireScraper(),
        ExpofinquesScraper(),
        ClausScraper(),
        PisosAdScraper(),
        PisoscomScraper()
    ]
    
    print("Iniciando scrapers...")
    
    for scraper in scrapers:
        try:
            print(f"Ejecutando {scraper.__class__.__name__}...")
            scraper.run()
            print(f"{scraper.__class__.__name__} completado.")
        except Exception as e:
            print(f"Error en {scraper.__class__.__name__}: {e}")
            continue
    
    print("Todos los scrapers han terminado.")

if __name__ == "__main__":
    run_all_scrapers()