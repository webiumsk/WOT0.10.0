# Embedded file name: scripts/client/CustomEffectManager.py
import BigWorld
from AvatarInputHandler import mathUtils
import Math
import math
import material_kinds
from CustomEffect import PixieCache
_ENABLE_VALUE_TRACKER = False

class CustomEffectManager(object):
    _LEFT_TRACK = 1
    _RIGHT_TRACK = 2
    _DRAW_ORDER_IDX = 50

    def __init__(self, vehicle, engineState):
        if _ENABLE_VALUE_TRACKER:
            from helpers.ValueTracker import ValueTracker
            self.__vt = ValueTracker.instance()
        else:
            self.__vt = None
        self.__selectors = []
        self.__variableArgs = dict()
        self.__vehicle = vehicle
        self.__enabled = False
        self.__engineState = engineState
        self.__prevWaterHeight = None
        args = {}
        args['chassis'] = {}
        args['chassis']['model'] = self.__vehicle.appearance.modelsDesc['chassis']['model']
        args['hull'] = {}
        args['hull']['model'] = self.__vehicle.appearance.modelsDesc['hull']['model']
        args['drawOrderBase'] = CustomEffectManager._DRAW_ORDER_IDX
        for desc in self.__vehicle.typeDescriptor.hull['customEffects']:
            if desc is not None:
                selector = desc.create(args)
                if selector is not None:
                    self.__selectors.append(selector)

        for desc in self.__vehicle.typeDescriptor.chassis['customEffects']:
            if desc is not None:
                selector = desc.create(args)
                if selector is not None:
                    self.__selectors.append(selector)

        self.__createChassisCenterNodes()
        return

    def getParameter(self, name):
        return self.__variableArgs.get(name, 0.0)

    def destroy(self):
        for effectSelector in self.__selectors:
            effectSelector.destroy()

        if self.__vehicle.isPlayer:
            PixieCache.clear()
        self.__engineState = None
        return

    def enable(self, isEnabled):
        self.__enabled = isEnabled

    def stop(self):
        for effectSelector in self.__selectors:
            effectSelector.stop()

    def __createChassisCenterNodes(self):
        chassisModel = self.__vehicle.appearance.modelsDesc['chassis']['model']
        topRightCarryingPoint = self.__vehicle.typeDescriptor.chassis['topRightCarryingPoint']
        self.__enabled = True
        self.__trailParticleNodes = []
        self.__trailParticles = {}
        mMidLeft = Math.Matrix()
        mMidLeft.setTranslate((-topRightCarryingPoint[0], 0, 0))
        mMidRight = Math.Matrix()
        mMidRight.setTranslate((topRightCarryingPoint[0], 0, 0))
        self.__trailParticleNodes = [chassisModel.node('', mMidLeft), chassisModel.node('', mMidRight)]

    def getTrackCenterNode(self, trackIdx):
        return self.__trailParticleNodes[trackIdx]

    def update(self):
        if not self.__enabled:
            return
        else:
            apperance = self.__vehicle.appearance
            vehicleSpeed = self.__vehicle.filter.speedInfo.value[2]
            self.__variableArgs['speed'] = vehicleSpeed
            direction = 1 if vehicleSpeed >= 0.0 else -1
            self.__variableArgs['direction'] = direction
            self.__variableArgs['rotSpeed'] = self.__vehicle.filter.speedInfo.value[1]
            if self.__vehicle.filter.placingOnGround:
                leftHasContact = self.__vehicle.filter.numLeftTrackContacts > 0
                rightHasContact = self.__vehicle.filter.numRightTrackContacts > 0
            else:
                leftHasContact = not apperance.fashion.isFlyingLeft
                rightHasContact = not apperance.fashion.isFlyingRight
            matKindsUnderTracks = getCorrectedMatKinds(apperance)
            self.__variableArgs['deltaR'], self.__variableArgs['directionR'], self.__variableArgs['matkindR'] = self.__getScrollParams(vehicleSpeed, apperance.rightTrackScroll, rightHasContact, matKindsUnderTracks[CustomEffectManager._RIGHT_TRACK])
            self.__variableArgs['deltaL'], self.__variableArgs['directionL'], self.__variableArgs['matkindL'] = self.__getScrollParams(vehicleSpeed, apperance.leftTrackScroll, leftHasContact, matKindsUnderTracks[CustomEffectManager._LEFT_TRACK])
            filterVelocity = self.__vehicle.filter.velocity
            velocity2D = Math.Vector2(filterVelocity.x, filterVelocity.z)
            velLen = velocity2D.length
            if velLen > 1.0:
                vehicleDir = Math.Vector3(1.0, 0.0, 0.0)
                vehicleDir.setPitchYaw(self.__vehicle.pitch, self.__vehicle.yaw)
                vehicleDir.normalise()
                cosA = velocity2D.dot(Math.Vector2(vehicleDir.x, vehicleDir.z)) / velLen
                self.__variableArgs['hullAngle'] = math.acos(mathUtils.clamp(0.0, 1.0, math.fabs(cosA)))
            else:
                self.__variableArgs['hullAngle'] = 0.0
            self.__variableArgs['isUnderWater'] = 1 if apperance.isUnderwater else 0
            self.__correctWaterNodes()
            self.__variableArgs['gearUp'] = self.__engineState.gearUp
            self.__variableArgs['RPM'] = self.__engineState.rpm
            self.__variableArgs['engineLoad'] = self.__engineState.mode
            self.__variableArgs['engineStart'] = self.__engineState.starting
            self.__variableArgs['physicLoad'] = apperance.physicLoad
            for effectSelector in self.__selectors:
                effectSelector.update(self.__variableArgs)

            if self.__vt is not None and self.__vehicle.isPlayer:
                self.__vt.addValue2('speed', self.__variableArgs['speed'])
                self.__vt.addValue2('direction', self.__variableArgs['direction'])
                self.__vt.addValue2('rotSpeed', self.__variableArgs['rotSpeed'])
                self.__vt.addValue2('deltaR', self.__variableArgs['deltaR'])
                self.__vt.addValue2('deltaL', self.__variableArgs['deltaL'])
                self.__vt.addValue2('hullAngle', self.__variableArgs['hullAngle'])
                self.__vt.addValue2('isUnderWater', self.__variableArgs['isUnderWater'])
                if self.__variableArgs['matkindL'] > -1:
                    materialL = material_kinds.EFFECT_MATERIAL_INDEXES_BY_IDS[self.__variableArgs['matkindL']]
                    self.__vt.addValue('materialL', material_kinds.EFFECT_MATERIALS[materialL])
                else:
                    self.__vt.addValue('materialL', 'No')
                if self.__variableArgs['matkindR'] > -1:
                    materialR = material_kinds.EFFECT_MATERIAL_INDEXES_BY_IDS[self.__variableArgs['matkindR']]
                    self.__vt.addValue('materialR', material_kinds.EFFECT_MATERIALS[materialR])
                else:
                    self.__vt.addValue('materialR', 'No')
                self.__vt.addValue2('engineStart', self.__variableArgs['engineStart'])
                self.__vt.addValue2('gearUP', self.__variableArgs['gearUp'])
            return

    def __getScrollParams(self, vehicleSpeed, trackScroll, hasContact, matKindsUnderTrack):
        matKind = -1
        scrollDelta = 0.0
        if hasContact:
            if abs(trackScroll) > 0.1:
                if abs(vehicleSpeed) < 0.1:
                    scrollDelta = trackScroll
                else:
                    scrollDelta = trackScroll - vehicleSpeed
                    if trackScroll * vehicleSpeed > 0.0:
                        if scrollDelta * trackScroll < 0.0:
                            scrollDelta = 0.0
            matKind = matKindsUnderTrack
        scrollDelta = abs(scrollDelta)
        direction = 1 if trackScroll >= 0.0 else -1
        return (scrollDelta, direction, matKind)

    def __correctWaterNodes(self):
        waterHeight = 0.0 if not self.__vehicle.appearance.isInWater else self.__vehicle.appearance.waterHeight
        if waterHeight != self.__prevWaterHeight:
            position = self.__vehicle.position
            for effectSelector in self.__selectors:
                for node in effectSelector.effectNodes:
                    node.correctWater(position, waterHeight)

            self.__prevWaterHeight = waterHeight


def getCorrectedMatKinds(vehicleAppearance):
    correctedMatKinds = [ (material_kinds.WATER_MATERIAL_KIND if vehicleAppearance.isInWater else matKind) for matKind in vehicleAppearance.terrainMatKind ]
    return correctedMatKinds
