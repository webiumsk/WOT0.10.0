# Embedded file name: scripts/client/gui/customization_2_0/data_aggregator.py
import copy
from Event import Event
from gui import GUI_SETTINGS
from gui.game_control import getIGRCtrl
from helpers.i18n import makeString as _ms
from gui.shared import g_itemsCache as _g_itemsCache
from gui.shared.ItemsCache import CACHE_SYNC_REASON, g_itemsCache
from items.vehicles import g_cache as _g_vehiclesCache
from items.qualifiers import g_cache as _g_qualifiersCache
from CurrentVehicle import g_currentVehicle as _g_currentVehicle, g_currentVehicle
from elements import AvailableCamouflage, AvailableInscription, AvailableEmblem, InstalledCamouflage, InstalledInscription, InstalledEmblem, Qualifier, CamouflageQualifier

class CUSTOMIZATION_TYPE:
    CAMOUFLAGE = 0
    EMBLEM = 1
    INSCRIPTION = 2


SLOT_TYPE = {CUSTOMIZATION_TYPE.EMBLEM: 'player',
 CUSTOMIZATION_TYPE.INSCRIPTION: 'inscription'}
_TYPE_NAME = {'emblems': CUSTOMIZATION_TYPE.EMBLEM,
 'inscriptions': CUSTOMIZATION_TYPE.INSCRIPTION,
 'camouflages': CUSTOMIZATION_TYPE.CAMOUFLAGE}
_ITEM_CLASS = {CUSTOMIZATION_TYPE.EMBLEM: AvailableEmblem,
 CUSTOMIZATION_TYPE.INSCRIPTION: AvailableInscription,
 CUSTOMIZATION_TYPE.CAMOUFLAGE: AvailableCamouflage}
_MAX_HULL_SLOTS = 2
_MAX_TURRET_SLOTS = 2

class DataAggregator(object):

    def __init__(self):
        self.updated = Event()
        self.viewModel = []
        self.__installed = ()
        self.__availableItems = [{}, {}, {}]
        self.__displayedItems = [{}, {}, {}]
        self.__initialViewModel = ()
        self.__displayIgrItems = getIGRCtrl().getRoomType() == 2 and GUI_SETTINGS.igrEnabled
        self.__availableGroupNames = []
        self.__gatherDataForVehicle(CACHE_SYNC_REASON.DOSSIER_RESYNC, None)
        _g_itemsCache.onSyncCompleted += self.__gatherDataForVehicle
        return

    def fini(self):
        _g_currentVehicle.onChanged -= self.__gatherDataForVehicle
        self.__installed = None
        self.__availableItems = None
        self.__displayedItems = None
        self.__initialViewModel = None
        self.__availableGroupNames = None
        self.viewModel = None
        return

    @property
    def installed(self):
        return self.__installed

    @property
    def available(self):
        return self.__availableItems

    @property
    def displayed(self):
        return self.__displayedItems

    @property
    def initialViewModel(self):
        return self.__initialViewModel

    @property
    def availableGroupNames(self):
        return self.__availableGroupNames

    def __gatherDataForVehicle(self, updateReason, invalidItems):
        if updateReason in (CACHE_SYNC_REASON.DOSSIER_RESYNC, CACHE_SYNC_REASON.SHOP_RESYNC):
            curVehItem = _g_currentVehicle.item
            curVehDescr = curVehItem.descriptor
            curVehDict = {'camouflages': list(curVehDescr.camouflages),
             'emblems': list(curVehDescr.playerEmblems),
             'inscriptions': list(curVehDescr.playerInscriptions)}
            inDossier = (_g_itemsCache.items.getVehicleDossier(curVehItem.intCD).getBlock('camouflages'), _g_itemsCache.items.getVehicleDossier(curVehItem.intCD).getBlock('emblems'), _g_itemsCache.items.getVehicleDossier(curVehItem.intCD).getBlock('inscriptions'))
            rawItems = [_g_vehiclesCache.customization(curVehItem.nationID)['camouflages'], _g_vehiclesCache.playerEmblems()[1], _g_vehiclesCache.customization(curVehItem.nationID)['inscriptions']]
            itemGroups = (_g_vehiclesCache.customization(curVehItem.nationID)['camouflageGroups'], _g_vehiclesCache.playerEmblems()[0], _g_vehiclesCache.customization(curVehItem.nationID)['inscriptionGroups'])
            self.__availableGroupNames = []
            self.__displayedItems = [{}, {}, {}]
            self.__availableItems = [{}, {}, {}]
            inventoryItems = self.__setInventoryItems(rawItems)
            for cType in [CUSTOMIZATION_TYPE.CAMOUFLAGE, CUSTOMIZATION_TYPE.EMBLEM, CUSTOMIZATION_TYPE.INSCRIPTION]:
                groups = []
                uniqueGroups = []
                for key, value in itemGroups[cType].iteritems():
                    if cType == CUSTOMIZATION_TYPE.CAMOUFLAGE:
                        itemIDsInGroup = value['ids']
                        groupUserName = value['userString']
                        groupIsInShop = not key.startswith('IGR') or self.__displayIgrItems
                    else:
                        itemIDsInGroup = value[0]
                        groupUserName = _ms(value[1])
                        groupIsInShop = self.__groupIsInShop(key, cType)
                    if groupIsInShop and key not in uniqueGroups:
                        uniqueGroups.append(key)
                        groups.append((key, groupUserName))
                    for itemID in list(inDossier[cType]) + inventoryItems[cType].keys():
                        if itemID in itemIDsInGroup and key not in uniqueGroups:
                            uniqueGroups.append(key)
                            groups.append((key, groupUserName))

                self.__availableGroupNames.append(groups)
                self.__fillAvailableItems(cType, inDossier, rawItems, itemGroups)
                self.__fillDisplayedItems(cType, inventoryItems)

            installedRawItems = self.__setInstalledRawItems(curVehDescr)
            self.__installed = self.__setInstalledCustomization(curVehDescr.hull['emblemSlots'], curVehDescr.turret['emblemSlots'], installedRawItems)
            self.updated()

    def __setInstalledCustomization(self, vehicleHullSlots, vehicleTurretSlots, installedRawItems):
        installedHullEmblems = []
        installedTurretEmblems = []
        installedHullInscriptions = []
        installedTurretInscriptions = []
        hullEmblemSlotIdx = 0
        hullInscriptionSlotIdx = 0
        turretEmblemSlotIdx = 0
        turretInscriptionSlotIdx = 0
        for slot in vehicleHullSlots:
            if slot.type == SLOT_TYPE[CUSTOMIZATION_TYPE.EMBLEM]:
                installedHullEmblems.append(installedRawItems['emblems'][hullEmblemSlotIdx])
                hullEmblemSlotIdx += 1
            if slot.type == SLOT_TYPE[CUSTOMIZATION_TYPE.INSCRIPTION]:
                installedHullInscriptions.append(installedRawItems['inscriptions'][hullInscriptionSlotIdx])
                hullInscriptionSlotIdx += 1

        for slot in vehicleTurretSlots:
            if slot.type == SLOT_TYPE[CUSTOMIZATION_TYPE.EMBLEM]:
                installedTurretEmblems.append(installedRawItems['emblems'][_MAX_HULL_SLOTS + turretEmblemSlotIdx])
                turretEmblemSlotIdx += 1
            if slot.type == SLOT_TYPE[CUSTOMIZATION_TYPE.INSCRIPTION]:
                installedTurretInscriptions.append(installedRawItems['inscriptions'][_MAX_HULL_SLOTS + turretInscriptionSlotIdx])
                turretInscriptionSlotIdx += 1

        return ([ InstalledCamouflage(ic, 0) for ic in installedRawItems['camouflages'] ], [ InstalledEmblem(ihe, 0) for ihe in installedHullEmblems ] + [ InstalledEmblem(ite, 2) for ite in installedTurretEmblems ], [ InstalledInscription(ihi, 0) for ihi in installedHullInscriptions ] + [ InstalledInscription(iti, 2) for iti in installedTurretInscriptions ])

    def __setInstalledRawItems(self, curVehDescr):
        installedRawItems = {'camouflages': list(curVehDescr.camouflages),
         'emblems': list(curVehDescr.playerEmblems),
         'inscriptions': list(curVehDescr.playerInscriptions)}
        if self.__displayIgrItems:
            igrLayout = g_itemsCache.items.inventory.getIgrCustomizationsLayout()
            vehicleId = g_currentVehicle.item.invID
            igrRoomType = getIGRCtrl().getRoomType()
            igrVehDescr = []
            if vehicleId in igrLayout:
                if igrRoomType in igrLayout[vehicleId]:
                    igrVehDescr = igrLayout[vehicleId][igrRoomType]
            for key in igrVehDescr:
                for index in igrVehDescr[key]:
                    installedRawItems[key][index] = igrVehDescr[key][index]

        self.__initialViewModel = (installedRawItems['emblems'], installedRawItems['inscriptions'])
        self.viewModel = [copy.deepcopy(installedRawItems['camouflages']), copy.deepcopy(installedRawItems['emblems']), copy.deepcopy(installedRawItems['inscriptions'])]
        return installedRawItems

    def __setInventoryItems(self, rawItems):
        inventoryItems = [{}, {}, {}]
        inventoryCustomization = g_itemsCache.items.inventory.getItemsData('customizations')
        for isGold, itemsData in inventoryCustomization.iteritems():
            if itemsData:
                for key in (None, g_currentVehicle.item.intCD):
                    if key not in itemsData:
                        continue
                    typedItemsData = itemsData[key]
                    for cTypeName, items in typedItemsData.iteritems():
                        cType = _TYPE_NAME[cTypeName]
                        for item, itemNum in items.iteritems():
                            if cType != CUSTOMIZATION_TYPE.EMBLEM:
                                nationID, itemID = item
                            else:
                                nationID, itemID = None, item
                            allowedVehicles = []
                            if key is not None:
                                allowedVehicles.append(key)
                            if g_currentVehicle.item.nationID == nationID or cType == CUSTOMIZATION_TYPE.EMBLEM:
                                inventoryItems[cType][itemID] = [itemID,
                                 rawItems[cType][itemID],
                                 None,
                                 isGold,
                                 allowedVehicles,
                                 [],
                                 (isGold, itemNum)]

        return inventoryItems

    def __fillAvailableItems(self, cType, inDossier, rawItems, itemGroups):
        containerToFill = self.__availableItems[cType]
        groups = itemGroups[cType]
        class_ = _ITEM_CLASS[cType]
        availableRawItems = rawItems[cType]
        for itemID, availableRawItem in availableRawItems.iteritems():
            if cType != CUSTOMIZATION_TYPE.CAMOUFLAGE:
                if availableRawItem[7] in _g_qualifiersCache.qualifiers:
                    qualifier = Qualifier(_g_qualifiersCache.qualifiers[availableRawItem[7]])
                else:
                    qualifier = CamouflageQualifier('winter')
                allowedVehicles, notAllowedVehicles = groups[availableRawItem[0]][3], groups[availableRawItem[0]][4]
            else:
                groupName = availableRawItem['groupName']
                qualifier = CamouflageQualifier(groupName[3:] if groupName.startswith('IGR') else groupName)
                allowedVehicles, notAllowedVehicles = availableRawItem['allow'], availableRawItem['deny']
            containerToFill[itemID] = class_(itemID, availableRawItem, qualifier, itemID in inDossier[cType], allowedVehicles, notAllowedVehicles)

    def __fillDisplayedItems(self, cType, inventoryItems):
        containerToFill = self.__displayedItems[cType]
        for itemID, availableItem in self.__availableItems[cType].iteritems():
            if availableItem.isInDossier:
                containerToFill[itemID] = availableItem
            if itemID in inventoryItems[cType]:
                availableItem.setAllowedVehicles(inventoryItems[cType][itemID][4])
                availableItem.markIsInDossier()
                if inventoryItems[cType][itemID][6][0]:
                    availableItem.numberOfItems = inventoryItems[cType][itemID][6][1]
                else:
                    availableItem.numberOfDays = inventoryItems[cType][itemID][6][1]
            if availableItem.isAllowedForCurrentVehicle:
                if cType == CUSTOMIZATION_TYPE.CAMOUFLAGE:
                    groupName = itemID
                else:
                    groupName = availableItem.getGroup()
                if itemID in inventoryItems[cType]:
                    containerToFill[itemID] = availableItem
                elif self.__groupIsInShop(groupName, cType):
                    containerToFill[itemID] = availableItem

    def __groupIsInShop(self, groupName, cType):
        return [lambda group: group not in g_itemsCache.items.shop.getCamouflagesHiddens(g_currentVehicle.item.nationID), lambda group: group not in g_itemsCache.items.shop.getEmblemsGroupHiddens() and (group != 'group5' or self.__displayIgrItems), lambda group: group not in g_itemsCache.items.shop.getInscriptionsGroupHiddens(g_currentVehicle.item.nationID) and (group != 'IGR' or self.__displayIgrItems)][cType](groupName)
