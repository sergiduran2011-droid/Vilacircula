from __future__ import annotations

from pydantic import BaseModel, Field

SCHOOLS = ("Goar", "Torre-roja", "Josep Mestres", "Miramar", "Olímpia", "Sales")

MERCHANTS = (
    {
        "id": "osm-12752947043",
        "name": "Café Marco",
        "category": "Cafeterías",
        "type": "Cafetería · comercio local",
        "initials": "CM",
        "latitude": 41.3173588,
        "longitude": 2.0257551,
        "address": "Carrer de Guifré el Pelós, Barri de Sales, Viladecans",
        "source": "OpenStreetMap",
        "source_url": "https://www.openstreetmap.org/node/12752947043",
        "is_demo": False,
        "offer": "Ficha y ubicación proceden de OpenStreetMap; confirma las condiciones con el local.",
        "reward": "Sin recompensas verificadas todavía.",
    },
    {
        "id": "osm-11432296231",
        "name": "a.m bakery & coffee",
        "category": "Alimentación",
        "type": "Panadería y café · comercio local",
        "initials": "AM",
        "latitude": 41.3122261,
        "longitude": 2.0023559,
        "address": "Carrer de Can Trias, Can Guardiola, Viladecans",
        "source": "OpenStreetMap",
        "source_url": "https://www.openstreetmap.org/node/11432296231",
        "is_demo": False,
        "offer": "Ficha y ubicación proceden de OpenStreetMap; confirma las condiciones con el local.",
        "reward": "Sin recompensas verificadas todavía.",
    },
    {
        "id": "demo-papeleria",
        "name": "Papelería de ejemplo",
        "category": "Papelería",
        "type": "Papelería · ficha ilustrativa",
        "initials": "PE",
        "latitude": None,
        "longitude": None,
        "address": None,
        "source": "VilaCircula · ejemplo",
        "source_url": None,
        "is_demo": True,
        "offer": "Ficha ilustrativa; no representa un comercio adherido confirmado.",
        "reward": "Los descuentos de esta ficha son de demostración.",
    },
    {
        "id": "demo-moda",
        "name": "Moda Circular · ejemplo",
        "category": "Moda",
        "type": "Moda · ficha ilustrativa",
        "initials": "ME",
        "latitude": None,
        "longitude": None,
        "address": None,
        "source": "VilaCircula · ejemplo",
        "source_url": None,
        "is_demo": True,
        "offer": "Ficha ilustrativa; no representa un comercio adherido confirmado.",
        "reward": "Los descuentos de esta ficha son de demostración.",
    },
)

REWARDS = (
    {"id": "bread", "name": "2 € en pan artesano", "store": "a.m bakery & coffee", "merchant_id": "osm-11432296231", "cost": 50, "art": "bread", "icon": "croissant", "description": "Descuento ilustrativo; consulta condiciones en el local.", "is_demo": True},
    {"id": "coffee", "name": "Un café de la casa", "store": "Café Marco", "merchant_id": "osm-12752947043", "cost": 45, "art": "coffee", "icon": "coffee", "description": "Premio ilustrativo; consulta condiciones en el local.", "is_demo": True},
    {"id": "book", "name": "2 € en material escolar", "store": "Papelería de ejemplo", "merchant_id": "demo-papeleria", "cost": 50, "art": "book", "icon": "notebook-pen", "description": "Recompensa y comercio de demostración.", "is_demo": True},
    {"id": "market", "name": "Cesta de temporada", "store": "Comercio de alimentación · ejemplo", "merchant_id": "demo-papeleria", "cost": 80, "art": "market", "icon": "carrot", "description": "Recompensa de demostración.", "is_demo": True},
    {"id": "shirt", "name": "10% en moda circular", "store": "Moda Circular · ejemplo", "merchant_id": "demo-moda", "cost": 60, "art": "shirt", "icon": "shirt", "description": "Recompensa y comercio de demostración.", "is_demo": True},
    {"id": "plant", "name": "Planta aromática", "store": "Comercio de alimentación · ejemplo", "merchant_id": "demo-papeleria", "cost": 40, "art": "plant", "icon": "sprout", "description": "Recompensa de demostración.", "is_demo": True},
)

CASHIER_SEEDS = (
    ("caja.cafe-marco", "osm-12752947043"),
    ("caja.am-bakery", "osm-11432296231"),
    ("caja.papeleria-demo", "demo-papeleria"),
    ("caja.moda-demo", "demo-moda"),
)


class ProfileCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=32)
    school: str = Field(min_length=1, max_length=40)
    username: str = Field(min_length=3, max_length=24, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=10, max_length=128)


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=32)
    school: str = Field(min_length=1, max_length=40)


class LoginPayload(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class CredentialsUpdate(BaseModel):
    username: str = Field(min_length=3, max_length=24, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=10, max_length=128)
    current_password: str | None = Field(default=None, max_length=128)


class PasswordUpdate(BaseModel):
    password: str = Field(min_length=10, max_length=128)
    current_password: str | None = Field(default=None, max_length=128)


class CashierProvision(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    merchant_id: str = Field(min_length=1, max_length=64)


class RewardRedeem(BaseModel):
    reward_id: str = Field(min_length=1, max_length=40)


class CouponScan(BaseModel):
    code: str = Field(min_length=8, max_length=40, pattern=r"^VC-[A-Z0-9]+$")
