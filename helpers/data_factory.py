import base64
import os
import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

IMAGE_B64 = (
    b"iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAHElEQVQoU2NkgIAgFo2BgYGB4T8mBgwGJQwMAE2YCxY3E8VgAAAAAElFTkSuQmCC"
)


@dataclass
class StudentData:
    first_name: str
    last_name: str
    birthdate: str
    phone: str
    carnet: str
    email: str
    school_value: str = "3"
    user_type: str = "Estudiante"
    active: bool = True


def _choice(values):
    return random.choice(values)


def random_name_pair():
    nombres = ["Luis", "Ana", "Carlos", "Maria", "Fernanda", "Jose", "Diana", "Ricardo", "Valeria", "Hector"]
    apellidos = ["Gonzalez", "Ramirez", "Hernandez", "Lopez", "Flores", "Martinez", "Castro", "Morales", "Vargas"]
    return _choice(nombres), _choice(apellidos)


def random_birthdate():
    inicio, fin = datetime(1990, 1, 1), datetime(2005, 12, 31)
    fecha = inicio + timedelta(days=random.randrange((fin - inicio).days))
    return fecha.strftime("%d/%m/%Y")


def random_phone():
    return f"7{random.randint(1000000, 9999999)}"


def random_carnet():
    letras = "".join(random.choice(string.ascii_uppercase) for _ in range(2))
    anio = random.randint(50, 60)
    numero = random.randint(800, 999)
    return f"{letras}{anio:02d}{numero:03d}"


def student_data(carnet: str | None = None) -> StudentData:
    nombre, apellido = random_name_pair()
    carnet = carnet or random_carnet()
    correo = f"{carnet.lower()}@ues.edu.sv"
    return StudentData(
        first_name=nombre,
        last_name=apellido,
        birthdate=random_birthdate(),
        phone=random_phone(),
        carnet=carnet,
        email=correo,
    )


def random_school_name():
    sufijo = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"Escuela de Prueba {sufijo}"


def random_resource_name():
    sufijo = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"Recurso de Prueba {sufijo}"


def random_description(prefix: str = "Reporte automatico QA", *, length: int = 6):
    sufijo = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix} {sufijo}"


def ensure_test_image(filename: str = "imagen_prueba.png") -> Path:
    ruta = Path(filename).resolve()
    if not ruta.exists():
        data = base64.b64decode(IMAGE_B64)
        ruta.write_bytes(data)
    return ruta
