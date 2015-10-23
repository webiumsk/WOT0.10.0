# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/clans/profile/ClanProfileFortificationView.py
import weakref
from adisp import process
from gui.Scaleform.daapi.view.lobby.clans.profile import data_receivers
from gui.Scaleform.daapi.view.lobby.clans.profile.ClanProfileBaseView import ClanProfileBaseView
from gui.Scaleform.genConsts.CLANS_ALIASES import CLANS_ALIASES

class ClanProfileFortificationView(ClanProfileBaseView):

    def __init__(self):
        super(ClanProfileFortificationView, self).__init__()
        self._fortDP = None
        return

    @process
    def setClanDossier(self, clanDossier):
        super(ClanProfileFortificationView, self).setClanDossier(clanDossier)
        self._showWaiting()
        if clanDossier.isMyClan():
            self._fortDP = data_receivers.OwnClanDataReceiver()
        else:
            self._fortDP = data_receivers.ClanDataReceiver()
        hasFort = yield self._fortDP.hasFort(clanDossier)
        clanInfo = yield clanDossier.requestClanInfo()
        if self.isDisposed():
            return
        self._updateClanInfo(clanInfo)
        if hasFort:
            linkage = CLANS_ALIASES.CLAN_PROFILE_FORT_INFO_VIEW_LINKAGE
        else:
            linkage = CLANS_ALIASES.CLAN_PROFILE_FORT_PROMO_VIEW_LINKAGE
        self.as_setDataS(linkage)
        self._updateHeaderState()
        self._hideWaiting()

    def showWaiting(self):
        self._showWaiting()

    def hideWaiting(self):
        self._hideWaiting()

    def _dispose(self):
        self._fortDP = None
        super(ClanProfileFortificationView, self)._dispose()
        return

    def _onRegisterFlashComponent(self, viewPy, alias):
        if alias in (CLANS_ALIASES.CLAN_PROFILE_FORT_INFO_VIEW_ALIAS, CLANS_ALIASES.CLAN_PROFILE_FORT_PROMO_VIEW_ALIAS):
            viewPy.setProxy(self, weakref.proxy(self._fortDP), self._clanDossier)
