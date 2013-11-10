__author__ = 'Williewonka-2013'
__version__ = 0.9

from cx_Freeze import setup, Executable

setup(
    name="KolibriClient",
    version = str(__version__),
    description = "Client for kolibri chat program",
    executables = [Executable("Client.py"), Executable("Server.py")]
)