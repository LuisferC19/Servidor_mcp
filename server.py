import os                              # Para leer variables de entorno (las del .env)
import mysql.connector                 # Librería para conectarnos a MySQL
from mysql.connector import Error      # Clase de error específica de MySQL, para atraparla en los try/except
from dotenv import load_dotenv         # Nos permite cargar el archivo .env a las variables de entorno
from fastmcp import FastMCP            # Framework para crear el servidor MCP
from openai import OpenAI              # Cliente de OpenAI, lo usamos también para Groq porque comparten el mismo formato

# Cargamos las variables del .env
load_dotenv()                          # Lee el archivo .env y mete sus valores en el entorno para poder usarlos con os.getenv()

mcp = FastMCP("Servidor Demo")         # Creamos la instancia del servidor MCP y le damos un nombre


def conectar_bd():
    """Crea y regresa una conexión a la base de datos usando datos del .env"""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),         # Dirección del servidor de MySQL ("localhost")
        port=os.getenv("DB_PORT"),         # Puerto donde escucha MySQL ( 3306)
        user=os.getenv("DB_USER"),         # Usuario con el que nos conectamos ("root")
        password=os.getenv("DB_PASSWORD"), # Contraseña de ese usuario
        database=os.getenv("DB_NAME"),     # Nombre de la base de datos a la que nos conectamos
    )
    # Esta función no hace nada por sí sola, solo regresa la conexión lista para usarse en otras funciones


@mcp.tool                              # Esta etiqueta convierte la función de abajo en una herramienta que el MCP puede exponer
def suma(a: int, b: int) -> int:
    """Suma dos números"""
    return a + b                       # Simplemente regresa el resultado de sumar los dos parámetros


@mcp.tool
def saludar(nombre: str) -> str:
    return f"Hola {nombre}"            # Regresa un saludo armado con el nombre que le mandaron


@mcp.tool
def crear_archivo(nombre_archivo: str, contenido: str) -> str:
    """Crea un archivo de texto con el contenido especificado."""
    try:
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:  # Abre (o crea) el archivo en modo escritura
            archivo.write(contenido)                                   # Escribe el contenido que nos pasaron dentro del archivo
        return f"Archivo '{nombre_archivo}' creado correctamente"       # Si todo salió bien, regresamos un mensaje de éxito

    except Exception as e:                          # Si algo falla (ruta inválida, permisos, etc.)
        return f"Error: {str(e)}"                    # Regresamos el error como texto, sin tronar el servidor


@mcp.tool
def consultar_bd(consulta: str) -> str:
    """Ejecuta una consulta SQL de tipo SELECT y regresa los resultados."""
    try:
        conexion = conectar_bd()               # Abrimos una conexión nueva usando la función que ya definimos arriba
        cursor = conexion.cursor()             # El cursor es lo que nos permite ejecutar comandos SQL sobre esa conexión
        cursor.execute(consulta)               # Ejecuta el SQL que nos mandaron como parámetro (ej. un SELECT)
        resultados = cursor.fetchall()         # Trae todas las filas que regresó la consulta
        cursor.close()                         # Cerramos el cursor porque ya no lo necesitamos
        conexion.close()                       # Cerramos la conexión a la base de datos para no dejarla abierta
        return str(resultados)                 # Convertimos los resultados a texto para poder regresarlos

    except Error as e:                                     # Si hay un error específico de MySQL (mala sintaxis, tabla inexistente, etc.)
        return f"Error de base de datos: {str(e)}"          # Regresamos el mensaje de error como texto


# Cliente para Groq
cliente_ia = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),           # La API key de Groq, leída del .env
    base_url="https://api.groq.com/openai/v1"    # Le decimos al cliente que apunte a los servidores de Groq en vez de OpenAI
)
# Este cliente se crea una sola vez cuando arranca el servidor, y todas las llamadas a la IA lo van a reutilizar


@mcp.tool
def preguntar_ia(pregunta: str) -> str:
    """Envía una pregunta a la IA (Groq/Llama) y regresa la respuesta generada."""
    try:
        respuesta = cliente_ia.chat.completions.create(
            model="llama-3.3-70b-versatile",         # El modelo de IA que va a responder (Llama 3.3 de 70B parámetros)
            messages=[
                {"role": "system", "content": "Eres un asistente útil y conciso."},  # Instrucción general de cómo debe comportarse la IA
                {"role": "user", "content": pregunta}                                # La pregunta que nos mandó quien usa la herramienta
            ],
            max_tokens=500,                            # Límite de qué tan larga puede ser la respuesta
        )
        return respuesta.choices[0].message.content    # De toda la respuesta, sacamos solo el texto generado por la IA

    except Exception as e:                              # Si falla la conexión, la API key está mal, no hay saldo, etc.
        return f"Error al consultar la IA: {str(e)}"     # Regresamos el error como texto en vez de tronar el servidor


if __name__ == "__main__":            # Esto solo se ejecuta si corres este archivo directamente (no si lo importas desde otro)
    mcp.run()                          # Arranca el servidor MCP y lo deja escuchando/atendiendo peticiones