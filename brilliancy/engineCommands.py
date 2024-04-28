from chess import engine

def configureEngine(engineName: str, uci_options: dict) -> engine:
    """
    This method configures a chess engine with the given UCI options and returns the 
    engine.
    engineName: str
        The name of the engine (or the command to start the engine)
    uci_optins: dict
        A dictionary containing the UCI options used for the engine
    return -> engine
        A configuered chess.engine
    """
    eng = engine.SimpleEngine.popen_uci(engineName)
    for k, v in uci_options.items():
        eng.configure({k:v})

    return eng
