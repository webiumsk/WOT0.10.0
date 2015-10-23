# Embedded file name: scripts/client/gui/miniclient/lobby/user_cm_handlers.py
from gui.Scaleform.daapi.view.lobby.user_cm_handlers import USER
from helpers import aop

class UserCmClanUnavailableAspect(aop.Aspect):

    def atReturn(self, cd):
        original_return_options = cd.returned
        for item in original_return_options:
            if item['id'] == USER.CLAN_INFO:
                if not item['initData']:
                    item['initData'] = {}
                item['initData']['enabled'] = False
                break

        return original_return_options


class UserCmClanUnavailablePointCut(aop.Pointcut):

    def __init__(self):
        aop.Pointcut.__init__(self, 'gui.Scaleform.daapi.view.lobby.user_cm_handlers', 'BaseUserCMHandler', '_addClanProfileInfo', aspects=(UserCmClanUnavailableAspect,))
