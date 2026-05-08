from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.main import EnvSettingsSource


def _parse_list(v):
    """Accept JSON strings, plain comma-separated strings, or lists."""
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        import json

        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        return [s.strip() for s in v.split(",") if s.strip()]
    return v


def _parse_dict(v):
    """Accept JSON strings, Python-literal strings, or dicts."""
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        if not v.strip():
            return {}
        import json

        try:
            parsed = json.loads(v)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        try:
            import ast

            parsed = ast.literal_eval(v)
            if isinstance(parsed, dict):
                return parsed
        except (ValueError, SyntaxError):
            pass
    return v


class Settings(BaseSettings):
    api_health_token: str = ""

    app_env: str = "prod"

    auth_access_token_expire_minutes: int = 480
    auth_algorithm: str = "HS256"
    auth_secret: str = ""

    contact_mail: str = "support@inett.de"
    contact_name: str = "inett GmbH"
    contact_url: str = "https://inett.de"

    cors_credentials: bool = False
    docs_enabled: bool = False
    cors_expose_headers: list = [
        "Retry-After",
        "X-Process-Time",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "X-Request-Id",
    ]
    cors_headers: list = [
        "Authorization",
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
    ]
    cors_methods: list = ["DELETE", "GET", "HEAD", "OPTIONS", "POST", "PUT"]
    cors_origins: list = []

    @field_validator(
        "cors_expose_headers",
        "cors_headers",
        "cors_methods",
        "cors_origins",
        "oidc_allowed_redirect_urls",
        mode="before",
    )
    @classmethod
    def _parse_list_fields(cls, v):
        return _parse_list(v)

    events_end_prep_time_days: int = 7
    events_start_prep_time_days: int = 7
    events_start_require_students: bool = False

    guacamole_conn_timezone: str = "Europe/Berlin"
    guacamole_connections_prefix: str = ""
    guacamole_connections_prefix_events: bool = False
    guacamole_db: str = "mysql"
    guacamole_password: str = "kvs"
    guacamole_rdp_color_depth: int | None = None
    guacamole_rdp_disable_bitmap_caching: bool = False
    guacamole_rdp_disable_download: bool = True
    guacamole_rdp_disable_gfx: bool = False
    guacamole_rdp_disable_offscreen_caching: bool = False
    guacamole_rdp_disable_upload: bool = True
    guacamole_rdp_enable_audio_input: bool = False
    guacamole_rdp_enable_desktop_composition: bool = False
    guacamole_rdp_enable_drive: bool = False
    guacamole_rdp_enable_font_smoothing: bool = False
    guacamole_rdp_enable_full_window_drag: bool = True
    guacamole_rdp_enable_menu_animations: bool = False
    guacamole_rdp_enable_printing: bool = False
    guacamole_rdp_enable_theming: bool = False
    guacamole_rdp_enable_wallpaper: bool = True
    guacamole_rdp_ignore_cert: bool = True
    guacamole_rdp_printer_name: str = "Printer-Name"
    guacamole_rdp_resize_method: str = "reconnect"
    guacamole_rdp_security: str = ""
    guacamole_rdp_server_layout: str = "de-de-qwertz"
    guacamole_sftp_server_alive_interval: int = 30
    guacamole_ssh_server_alive_interval: int = 30
    guacamole_url: str = "https://localhost"
    guacamole_user: str = "OpenVLE"
    guacamole_vnc_color_depth: int = 32

    ldap_attr_mail: str = "mail"
    ldap_attr_user: str = "uid"
    ldap_dn_people: str = ""
    ldap_enabled: bool = False
    ldap_host: str = "localhost"
    ldap_port: int = 389
    ldap_verify_ssl: bool = True

    mail_max_age_weeks: int = 4

    moodle_enabled: bool = False
    moodle_url: str = ""
    moodle_token: str = ""
    moodle_verify_ssl: bool = True
    moodle_timeout: int = 30
    moodle_sync_timeout: int = 10
    moodle_user_auth: str = "ldap"
    moodle_user_match_field: str = "email"
    moodle_course_visible: bool = True
    moodle_delete_course_on_event_delete: bool = False

    mariadb_charset: str = "utf8mb4"
    mariadb_database: str = "database"
    mariadb_host: str = "localhost"
    mariadb_password: str = "password"
    mariadb_pool_acquire: int = 7000
    mariadb_pool_enabled: bool = True
    mariadb_pool_idle: int = 250000
    mariadb_pool_max: int = 12
    mariadb_pool_min: int = 2
    mariadb_port: int = 3306
    mariadb_query_result_limit: int = 200
    mariadb_timeout: int = 5
    mariadb_type: str = "mariadb"
    mariadb_user: str = "username"

    mongodb_database: str = "database"
    mongodb_host: str = "localhost"
    mongodb_password: str = "db_password"
    mongodb_port: int = 27017
    mongodb_user: str = "username"

    oidc_allowed_redirect_urls: list = []
    oidc_attr_email: str = "email"
    oidc_attr_name: str = "name"
    oidc_attr_username: str = "sub"
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_enabled: bool = False
    oidc_enroll_users: bool = True
    oidc_scopes: str = "openid email profile"
    oidc_url_metadata: str = ""

    project_description: str = "description"
    project_name: str = "name"
    project_title: str = "title"
    project_version: float = 1.0

    pve_api_poll_rate: int = 5
    pve_ci_enabled: bool = False
    pve_ci_drive: str = "cephssd"
    pve_fqdn: str = "domain.intern"
    pve_hostname: str = "proxmox:8006"
    pve_token_name: str = "my-token"
    pve_token_value: str = "my-token-secret"
    pve_user: str = "user@pve"
    pve_verify_ssl: bool = True
    pve_vm_subnet: str = "0.0.0.0/16"
    pve_vms_ciupgrade: bool = False
    pve_vms_cipassword: str = ""
    pve_vms_ciuser: str = "user"
    pve_vms_dns_domain: str = ""
    pve_vms_dns_server: str = "1.1.1.1"
    pve_vms_excluded_ips: str = (
        "172.20.0.200,172.20.0.1-172.20.0.254,172.20.100.0/24"
    )
    pve_vms_full_clone_default: bool = False
    pve_vms_gateway: str = ""
    pve_vms_network: str = ""
    pve_vms_pool: str = "KVS-VMs"
    pve_vms_smbios_metadata: bool = True
    pve_vms_subnet: str = "/24"

    redis_database: int = 0
    redis_host: str = "localhost"
    redis_password: str = "password"
    redis_port: int = 6379
    redis_username: str = "username"

    sentry_backend_dsn: str = ""
    sentry_backend_enable_tracing: bool = True
    sentry_backend_enabled: bool = False
    sentry_backend_profiles_sample_rate: float = 1.0
    sentry_backend_traces_sample_rate: float = 1.0
    sentry_env: str = "dev"
    sentry_release: str = ""
    sentry_worker_dsn: str = ""
    sentry_worker_enable_tracing: bool = True
    sentry_worker_enabled: bool = False
    sentry_worker_profiles_sample_rate: float = 1.0
    sentry_worker_traces_sample_rate: float = 1.0

    session_secret_token: str = ""

    smtp_from_mail: str = "kvs@example.com"
    smtp_from_name: str = "KVS"
    smtp_host: str = "localhost"
    smtp_method: str = "ssl"
    smtp_password: str = ""
    smtp_port: int = 465
    smtp_username: str = ""

    worker_max_retry: int = 5
    worker_pve_periodic_interval: int = 60

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Env vars first, then .env file (lenient: skip unparsable values)."""
        from pydantic_settings import DotEnvSettingsSource

        class LenientEnvSource(EnvSettingsSource):
            def decode_complex_value(self, field_name, field, value):
                """Fall back to raw string if JSON decode fails."""
                try:
                    return super().decode_complex_value(
                        field_name, field, value
                    )
                except Exception:
                    return value

        class LenientDotEnvSource(DotEnvSettingsSource):
            def decode_complex_value(self, field_name, field, value):
                """Fall back to raw string if JSON decode fails."""
                try:
                    return super().decode_complex_value(
                        field_name, field, value
                    )
                except Exception:
                    return value

            def __call__(self):
                try:
                    return super().__call__()
                except Exception:
                    return {}

        return (
            init_settings,
            LenientEnvSource(settings_cls),
            LenientDotEnvSource(settings_cls),
        )
