"""Typed representations of Jellyfin API payloads."""
from __future__ import annotations

from typing import List, Optional, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NameGuidPair(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Name: Optional[str] = Field(None, description="Display name")
    Id: Optional[str] = Field(None, description="Stable identifier")


class UserItemDataDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    PlayedPercentage: Optional[float] = Field(
        None, description="Completion percentage"
    )
    Played: Optional[bool] = Field(None, description="True when item is fully played")


class BaseItemDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Id: str
    Type: str
    Name: Optional[str] = None
    SeriesName: Optional[str] = None
    ParentIndexNumber: Optional[int] = None
    IndexNumber: Optional[int] = None
    DateCreated: Optional[str] = None
    PremiereDate: Optional[str] = None
    RunTimeTicks: Optional[int] = None
    Studios: Optional[List[NameGuidPair]] = None
    Genres: Optional[List[str]] = None
    UserData: Optional[UserItemDataDto] = None
    Taglines: Optional[List[str]] = None
    ProviderIds: Optional[dict] = None
    Artists: Optional[List[str]] = None
    CommunityRating: Optional[float] = None
    CriticRating: Optional[float] = None
    DateLastMediaAdded: Optional[str] = None
    OfficialRating: Optional[str] = None

    @field_validator("RunTimeTicks")
    @classmethod
    def non_negative_runtime(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 0:
            raise ValueError("RunTimeTicks must be non-negative")
        return value


class BaseItemDtoQueryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Items: List[BaseItemDto]
    TotalRecordCount: int
    StartIndex: Optional[int] = None


class UpcomingCardDefaults(TypedDict):
    title_default: str
    line1_default: str
    line2_default: str
    line3_default: str
    line4_default: str
    icon: str


class UpcomingCardItem(TypedDict):
    title: str
    episode: str
    flag: bool
    airdate: Optional[str]
    number: Optional[str]
    runtime: Optional[int]
    studio: Optional[str]
    release: Optional[str]
    poster: Optional[str]
    fanart: Optional[str]
    genres: Optional[str]
    rating: Optional[str]
    stream_url: Optional[str]
    info_url: Optional[str]


UpcomingCardPayload = List[UpcomingCardDefaults | UpcomingCardItem]


class YamcCardDefaults(TypedDict):
    title_default: str
    line1_default: str
    line2_default: str
    line3_default: str
    line4_default: str
    line5_default: str
    text_link_default: str
    link_default: str


class YamcCardItem(TypedDict):
    id: str
    type: str
    title: str
    episode: Optional[str]
    tagline: Optional[str]
    flag: bool
    airdate: Optional[str]
    number: Optional[str]
    runtime: Optional[int]
    studio: Optional[str]
    release: Optional[str]
    poster: Optional[str]
    fanart: Optional[str]
    genres: Optional[str]
    progress: Optional[float]
    rating: Optional[str]
    info: Optional[str]
    stream_url: Optional[str]
    info_url: Optional[str]


YamcCardPayload = List[YamcCardDefaults | YamcCardItem]
