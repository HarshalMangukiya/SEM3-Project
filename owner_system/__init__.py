# Owner System Module
# Flask Blueprint for owner-related functionality

from flask import Blueprint

# Create the owner_system blueprint
owner_bp = Blueprint('owner_system', __name__, 
                     template_folder='templates',
                     url_prefix='')

# Import routes after blueprint creation to avoid circular imports
from . import routes
