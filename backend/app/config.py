"""Configuração lida de variáveis de ambiente (RNF13: segredos fora do repositório)."""
import os


def _e(chave: str, padrao: str) -> str:
    return os.environ.get(chave, padrao)


class Settings:
    mqtt_host = _e("MQTT_HOST", "localhost")
    mqtt_port = int(_e("MQTT_PORT", "1883"))
    mqtt_user = _e("MQTT_USER", "dsm")
    mqtt_pass = _e("MQTT_PASS", "dsm_pass")
    database_url = _e("DATABASE_URL", "postgresql://dsm:dsm@localhost:5432/dsm")
    jwt_secret = _e("JWT_SECRET", "trocar-esta-chave-em-producao-0123456789")
    admin_user = _e("ADMIN_USER", "admin")
    admin_pass = _e("ADMIN_PASS", "admin123")
    ambiente = _e("DSM_ENV", "prod")


settings = Settings()
