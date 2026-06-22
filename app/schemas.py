from pydantic import BaseModel, Field


class ScanRecord(BaseModel):
    url: str
    score: int = Field(ge=0, le=100)
    ssl_valid: bool
    domain_age_days: int | None
    google_safe: bool
    details: str
    scanned_at: float


class StatsResponse(BaseModel):
    total_scans: int
    safe_count: int
    suspicious_count: int
    dangerous_count: int
    average_score: float


class HistoryResponse(BaseModel):
    items: list[ScanRecord]
    total: int
    page: int
    page_size: int
