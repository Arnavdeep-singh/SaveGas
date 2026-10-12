from pydantic import BaseModel, ConfigDict, Field


class StationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    brand: str = Field(min_length=1, max_length=100)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class StationResponse(StationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
