from .CuraMcpBridge import CuraMcpBridge


def getMetaData():
    return {}


def register(app):
    return {"extension": CuraMcpBridge()}
