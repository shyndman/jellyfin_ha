"""Implement a view to provide proxied Jellyfin thumbnails to the media browser."""

from __future__ import annotations

from http import HTTPStatus
import logging

from aiohttp import web
from aiohttp.hdrs import CACHE_CONTROL
from aiohttp.typedefs import LooseHeaders

from homeassistant.components.http import KEY_AUTHENTICATED, KEY_HASS, HomeAssistantView
from homeassistant.components.media_player import async_fetch_image

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class JellyfinImageView(HomeAssistantView):
    """View to serve proxied Jellyfin images."""

    name = "api:jellyfin:image"
    url = "/api/jellyfin_image_proxy/{entry_id}/{media_content_id}"

    async def get(
        self,
        request: web.Request,
        entry_id: str,
        media_content_id: str,
    ) -> web.Response:
        """Handle GET request for a Jellyfin image."""
        if not request[KEY_AUTHENTICATED]:
            return web.Response(status=HTTPStatus.UNAUTHORIZED)

        hass = request.app[KEY_HASS]

        # Find the manager for this entry
        manager = None
        for url, data in hass.data.get(DOMAIN, {}).items():
            if isinstance(data, dict) and data.get("entry_id") == entry_id:
                manager = data.get("manager")
                break

        if manager is None:
            _LOGGER.debug("No Jellyfin manager found for entry_id: %s", entry_id)
            return web.Response(status=HTTPStatus.NOT_FOUND)

        # Get the cached image URL
        image_url = manager.thumbnail_cache.get(media_content_id)
        if image_url is None:
            _LOGGER.debug("No cached thumbnail for media_content_id: %s", media_content_id)
            return web.Response(status=HTTPStatus.NOT_FOUND)

        # Fetch the image through HA (which can reach Jellyfin)
        data, content_type = await async_fetch_image(_LOGGER, hass, image_url)

        if data is None:
            return web.Response(status=HTTPStatus.SERVICE_UNAVAILABLE)

        headers: LooseHeaders = {CACHE_CONTROL: "max-age=3600"}
        return web.Response(body=data, content_type=content_type, headers=headers)


def get_proxy_image_url(entry_id: str, media_content_id: str) -> str:
    """Generate a proxied image URL for the media browser."""
    return f"/api/jellyfin_image_proxy/{entry_id}/{media_content_id}"
