"""Vacío a propósito: su sola presencia hace que pytest agregue la raíz
del proyecto a sys.path, para poder hacer `import core...`, `import
interface...` y `import config` desde tests/ sin instalar el proyecto
como paquete.
"""
