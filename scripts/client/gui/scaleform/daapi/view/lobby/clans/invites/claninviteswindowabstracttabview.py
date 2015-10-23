# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/clans/invites/ClanInvitesWindowAbstractTabView.py
from gui.Scaleform.daapi.view.meta.ClanInvitesWindowAbstractTabViewMeta import ClanInvitesWindowAbstractTabViewMeta
from gui.Scaleform.locale.CLANS import CLANS
from gui.Scaleform.genConsts.CLANS_ALIASES import CLANS_ALIASES
from gui.clans.clan_helpers import ClanListener
from helpers.i18n import makeString as _ms
from gui.shared.utils.functions import makeTooltip

class ClanInvitesWindowAbstractTabView(ClanInvitesWindowAbstractTabViewMeta, ClanListener):

    def __init__(self):
        super(ClanInvitesWindowAbstractTabView, self).__init__()
        self.__filterName = self._getDefaultFilterName()

    @property
    def paginatorsController(self):
        return self._parentWnd.paginatorsController

    @property
    def currentFilterName(self):
        return self.__filterName

    @property
    def clanInfo(self):
        return self._parentWnd.clanInfo

    def resyncClanInfo(self, force = False):
        return self._parentWnd.resyncClanInfo(force=force)

    def showMore(self):
        self._sendShowMoreRequest(self._getCurrentPaginator())

    def refreshTable(self):
        self._enableRefreshBtn(False)
        self.resyncClanInfo(force=True)
        self.paginatorsController.markPanginatorsAsUnSynced()
        self._sendRefreshRequest(self._getCurrentPaginator())

    def filterBy(self, filterName):
        self.__filterName = filterName
        paginator = self._getCurrentPaginator()
        if paginator.isSynced():
            self._onListUpdated(None, True, True, (paginator.getLastStatus(), paginator.getLastResult()))
        else:
            self._sendRefreshRequest(paginator)
        return

    def onSortChanged(self, dataProvider, sort):
        order = sort[0][1]
        secondSort = tuple(((item, order) for item in self._getSecondSortFields()))
        self._sendSortRequest(self._getCurrentPaginator(), sort + secondSort)

    def onClanAppsCountReceived(self, clanDbID, appsCount):
        super(ClanInvitesWindowAbstractTabView, self).onClanAppsCountReceived(clanDbID, appsCount)
        self._enableRefreshBtn(True)

    def onClanInvitesCountReceived(self, clanDbID, appsCount):
        super(ClanInvitesWindowAbstractTabView, self).onClanAppsCountReceived(clanDbID, appsCount)
        self._enableRefreshBtn(True)

    def formatInvitesCount(self, paginator):
        return self._parentWnd.formatInvitesCount(paginator)

    def showWaiting(self, show):
        self._parentWnd.showWaiting(show)

    def _getViewAlias(self):
        raise NotImplementedError

    def _getDummyByFilterName(self, filterName):
        raise NotImplementedError

    def _getDefaultFilterName(self):
        raise NotImplementedError

    def _makeFilters(self):
        raise NotImplementedError

    def _getSecondSortFields(self):
        return tuple()

    def _onListUpdated(self, selectedID, isFullUpdate, isReqInCoolDown, result):
        self._updateFiltersState()
        paginator = self._getCurrentPaginator()
        self._updateSortField(paginator.getLastSort() or self._getDefaultSortFields())
        status, data = result
        if status is True:
            self._enableRefreshBtn(False)
            if len(data) == 0:
                self.as_showDummyS(self._getDummyByFilterName(self.currentFilterName))
                self.dataProvider.rebuildList(None, False)
            else:
                self.dataProvider.rebuildList(data, paginator.canMoveRight())
                self.as_hideDummyS()
        else:
            self._enableRefreshBtn(True, toolTip=CLANS.CLANINVITESWINDOW_TOOLTIPS_REFRESHBUTTON_ENABLEDTRYTOREFRESH)
            self.as_showDummyS(CLANS_ALIASES.INVITE_WINDOW_DUMMY_SERVER_ERROR)
        self.showWaiting(False)
        return

    def _onListItemsUpdated(self, paginator, items):
        currentPaginator = self._getCurrentPaginator()
        if currentPaginator == paginator:
            self.dataProvider.refreshItems(items)

    def _getPaginatorByFilterName(self, filterName):
        return self.paginatorsController.getPanginator(self._getViewAlias(), filterName)

    def _getCurrentPaginator(self):
        return self._getPaginatorByFilterName(self.currentFilterName)

    def _sendResetRequest(self, paginator):
        if not paginator.isInProgress():
            self.showWaiting(True)
            paginator.reset()

    def _sendShowMoreRequest(self, paginator):
        if not paginator.isInProgress():
            self.showWaiting(True)
            paginator.right()

    def _sendRefreshRequest(self, paginator):
        self.showWaiting(True)
        if not paginator.isInProgress():
            paginator.refresh()
        else:
            self.showWaiting(False)

    def _sendSortRequest(self, paginator, sort):
        if not paginator.isInProgress():
            self.showWaiting(True)
            paginator.sort(sort)

    def _populate(self):
        self.startClanListening()
        super(ClanInvitesWindowAbstractTabView, self)._populate()

    def _dispose(self):
        self.stopClanListening()
        super(ClanInvitesWindowAbstractTabView, self)._dispose()

    def _onAttachedToWindow(self):
        super(ClanInvitesWindowAbstractTabView, self)._onAttachedToWindow()

    def _makeData(self):
        data = super(ClanInvitesWindowAbstractTabView, self)._makeData()
        data['filters'] = self._makeFilters()
        data['defaultFilter'] = self._getDefaultFilterName()
        return data

    def _updateFiltersState(self):
        for item in self._makeFilters():
            self.as_updateFilterStateS(item)

    def _enableRefreshBtn(self, enable, toolTip = None):
        if enable:
            self.as_updateButtonRefreshStateS(True, makeTooltip(body=_ms(toolTip or CLANS.CLANINVITESWINDOW_TOOLTIPS_REFRESHBUTTON_ENABLED)))
        else:
            self.as_updateButtonRefreshStateS(False, makeTooltip(body=_ms(toolTip or CLANS.CLANINVITESWINDOW_TOOLTIPS_REFRESHBUTTON_DISABLED)))
