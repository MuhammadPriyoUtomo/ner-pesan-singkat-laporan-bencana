# Import blueprints from other files
from .main_routes import main_bp
from .mode_routes import mode_bp
from .hasil_routes import hasil_bp
from .data_routes import data_bp
from .scraping_routes import scraping_bp
from .detection_routes import detection_bp
from .search_routes import search_bp
from .training_routes import training_bp
from .evaluation_routes import evaluation_bp
from .template_management_route import template_bp
from .lihat_data_model_route import data_model_bp
from .lihat_location_routes import lihat_location_bp
from .results_routes import results_bp

# List of all blueprints
blueprints = [main_bp, mode_bp, hasil_bp, data_bp, scraping_bp, detection_bp, search_bp, training_bp, evaluation_bp, template_bp, data_model_bp, lihat_location_bp, results_bp]