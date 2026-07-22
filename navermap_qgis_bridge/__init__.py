def classFactory(iface):
    from .plugin import NaverMapQgisBridgePlugin

    return NaverMapQgisBridgePlugin(iface)

