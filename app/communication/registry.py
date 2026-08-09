from app.communication.providers.openwa import OpenWAProvider

providers = {
    "openwa": OpenWAProvider(),
}

def get_provider(name="openwa"):
    return providers[name]