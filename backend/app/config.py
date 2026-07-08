from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ../.env covers running uvicorn from backend/ with the repo-root .env
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    # Data providers
    rentcast_api_key: str = ""
    census_api_key: str = ""  # optional; Census works keyless at low volume
    fred_api_key: str = ""

    # LLM — "anthropic" or "openai"; auto-picks whichever key is present
    llm_provider: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    openai_model: str = "gpt-4o"

    # Infra
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = ""  # e.g. postgresql://housefax:housefax@localhost:5432/housefax

    # Cache TTLs (seconds)
    provider_cache_ttl: int = 60 * 60 * 24 * 7  # RentCast/Census/FRED/FEMA responses
    report_cache_ttl: int = 60 * 60 * 24        # fully generated reports

    # Underwriting defaults (used when the user doesn't supply them)
    default_down_payment_pct: float = 0.20
    default_mortgage_rate: float = 0.07  # overridden by FRED 30yr average when available
    default_loan_term_years: int = 30
    default_vacancy_rate: float = 0.05
    default_property_tax_rate: float = 0.011
    default_insurance_rate: float = 0.005
    default_maintenance_rate: float = 0.01
    default_management_fee_rate: float = 0.08
    default_capex_reserve_rate: float = 0.05

    # Comp quality bounds (also enforced by the eval harness)
    comp_max_distance_miles: float = 1.5
    comp_sqft_band: float = 0.35  # comp sqft within ±35% of subject
    comp_max_age_months: int = 18

    def resolved_provider(self) -> str:
        if self.llm_provider:
            return self.llm_provider
        if self.anthropic_api_key:
            return "anthropic"
        if self.openai_api_key:
            return "openai"
        return "none"


@lru_cache
def get_settings() -> Settings:
    return Settings()
