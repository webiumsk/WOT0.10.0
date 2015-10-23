# Embedded file name: scripts/client/gui/miniclient/lobby/__init__.py
from gui.miniclient.lobby.user_cm_handlers import UserCmClanUnavailablePointCut
import tank_carousel
from hangar import configure_pointcuts as _configure_hangar_pointcuts
from header import configure_pointcuts as _configure_header_pointcuts
from tank_carousel import configure_pointcuts as _configure_carousel_pointcuts
from profile import configure_pointcuts as _configure_profile_pointcuts
from MiniclientDescriptionWindow import MiniclientDescriptionWindow

def configure_pointcuts(config):
    _configure_carousel_pointcuts(config)
    _configure_hangar_pointcuts(config)
    _configure_header_pointcuts(config)
    _configure_profile_pointcuts()
    MiniclientDescriptionWindow()
    UserCmClanUnavailablePointCut()
