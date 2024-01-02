"""LycheeThings API Client.

This is a python version of the great work done by
Jay Basen (https://github.com/jbasen/Crestron-SmartSlydr) to integrate
Lycheethings SmartSlydr devices into HomeAssistant.

"""
from __future__ import annotations


import traceback
from typing import ClassVar
import aiohttp

from marshmallow_dataclass import dataclass  # noqa: D100
from marshmallow import Schema

from .const import LOGGER, BASE_API_URL,DOMAIN

HEADERS = {
    "Accept-Encoding": "gzip",
    "User-Agent": "Mozilla/5.0",
}

@dataclass
class SmartSlydrDevice:
    """SmartSlydr Device Class Definition."""

    device_id: str
    devicename: str
    petpass: str
    room_name: str
    room_id: str
    wlansignal: int
    temperature: int
    humidity: int
    position: int
    error: str
    status: str
    Schema: ClassVar[type[Schema]] = Schema

class LycheeThingsApiClientError(Exception):
    """Exception to indicate a general API error."""


class LycheeThingsApiClientCommunicationError(
    LycheeThingsApiClientError
):
    """Exception to indicate a communication error."""


class LycheeThingsApiClientAuthenticationError(
    LycheeThingsApiClientError
):
    """Exception to indicate an authentication error."""


class LycheeThingsApiClient:
    """LycheeThings API Client."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize Class."""
        self.base_url = BASE_API_URL
        self.headers = HEADERS
        self.debug = True
        self.username = username
        self.password = password

        self.access_token = ""
        self.refresh_token = ""

        self._session = session

    def Debug_Message(self, name: str, message: str) -> None:  # noqa: D102
        if self.debug:
            LOGGER.debug(f"{DOMAIN} - {name}: {message}")  # noqa: G004

    ##****************************************************************************************
    #
    #       getSecurityTokens	-	Get Access and Security Tokens
    #
    ##****************************************************************************************

    async def getSecurityTokens(self):  # noqa: D102
        session = self._session

        # Create URL
        url = self.base_url + "auth"
        self.Debug_Message("Get_Security_Tokens", "URL: " + url)

        json = {"username": self.username ,"password": self.password  }

        self.Debug_Message("Get_Security_Tokens", "for user " + self.username)

        try:
            myheaders = self.headers
            myheaders["ContentType"] = "application/json"
            myheaders["Accept"] = "*/*"

            response = await session.post(url, headers=myheaders, json=json)

            if (response.status < 200) or (response.status >= 300):
                # server threw a error
                self.Debug_Message(
                    "Get_Security_Tokens",
                    "Error - response.status = " + str(response.status),
                )
                self.Debug_Message(
                    "Get_Security_Tokens", "Error - response.text= " + await response.text()
                )

                return False

            else:
                self.Debug_Message(
                    "Get_Security_Tokens",
                    "Success " + await response.text(),
                )

                jsonResponse = await response.json()
                self.access_token = jsonResponse["access_token"]

                # self.Debug_Message(
                #     "Get_Security_Tokens", "Access Token = " + self.access_token
                # )
                self.refresh_token = jsonResponse["refresh_token"]

                # self.Debug_Message(
                #     "Get_Security_Tokens", "Refresh Token = " + self.refresh_token
                # )

                return True

        except Exception as ex:
            LOGGER.error(
                f"{DOMAIN} Exception in getSecurityTokens : %s - traceback: %s",  # noqa: G004
                ex,
                traceback.format_exc(),
            )
        return False

    ##****************************************************************************************
    #
    #       Refresh_Access_Token	-	Get Access and Security Tokens
    #
    ##****************************************************************************************

    async def refreshAccessToken(self):  # noqa: D102
        session = self._session

        # Create URL
        url = self.base_url + "token"
        json = {"refresh_token": self.refresh_token}

        self.Debug_Message("refreshAccessToken", "URL: " + url)

        try:
            myheaders = self.headers
            myheaders["ContentType"] = "application/json"
            myheaders["Access Token"] = self.access_token
            myheaders["Accept"] = "*/*"

            response = await session.post(url, headers=myheaders, json=json)

            if (response.status < 200) or (response.status >= 300):
                # server threw a error
                self.Debug_Message(
                    "refreshAccessToken",
                    "Error - response.status = " + str(response.status),
                )
                self.Debug_Message(
                    "refreshAccessToken", "Error - response.text= " + await response.text()
                )

                return False

            else:
                # self.Debug_Message(
                #     "refreshAccessToken",
                #     "Success - response.ContentString = " + await response.text(),
                # )

                jsonResponse = await response.json()
                self.access_token = jsonResponse["access_token"]

                # self.Debug_Message(
                #     "refreshAccessToken", "Access Token = " + self.access_token
                # )

                return True

        except Exception as ex:
            LOGGER.error(
                f"{DOMAIN} Exception in refreshAccessToken : %s - traceback: %s",  # noqa: G004
                ex,
                traceback.format_exc(),
            )
        return False

    # ****************************************************************************************
    #
    #  getDeviceList	-	Gets the list of devices associated with an account
    #                       and print to console
    #
    # ****************************************************************************************

    async def getDeviceList(self):  # noqa: D102
        session = self._session

        await self.refreshAccessToken()

        # Create URL
        url = self.base_url + "devices"
        self.Debug_Message("GetDevicesList", "URL: " + url)

        try:
            myheaders = self.headers
            myheaders["ContentType"] = "application/json"
            myheaders["Authorization"] = self.access_token
            myheaders["Accept"] = "*/*"

            response = await session.get(url, headers=myheaders)

            if (response.status < 200) or (response.status >= 300):
                # server threw a error
                self.Debug_Message(
                    "getDeviceList",
                    "Error - response.status = " + str(response.status),
                )
                self.Debug_Message(
                    "getDeviceList", "Error - response.text= " + await response.text()
                )

                return False

            else:
                self.Debug_Message(
                    "getDeviceList",
                    "Success - response.ContentString = " + await response.text(),
                )

                jsonResponse = await response.json()

                Rooms = jsonResponse["room_lists"]

                Devices = {}

                for Room in Rooms:
                    deviceList = Room["device_list"]
                    for device in deviceList:
                        slydrDevice = SmartSlydrDevice.Schema().load(device)
                        Devices[slydrDevice.device_id] = slydrDevice
                    # Devices.append(SmartSlydrDevice.Schema().load(device))

                # self.access_token = jsonResponse["access_token"]

                # self.Debug_Message(
                #     "refreshAccessToken", "Access Token = " + self.access_token
                # )

                return Devices

        except Exception as ex:
            LOGGER.error(
                f"{DOMAIN} Exception in refreshAccessToken : %s - traceback: %s",  # noqa: G004
                ex,
                traceback.format_exc(),
            )
        return False

    # ****************************************************************************************
    #
    # 		setPosition	-	Set door position, 0 to 100
    #
    # ****************************************************************************************

    async def setPosition(self, device_id: str, position: int) -> None:  # noqa: D102
        if (position > 100) and (position != 200):
            self.Debug_Message(
                "setPosition", "Error - Position out of range: " + str(position)
            )
            return

        session = self._session
        await self.refreshAccessToken()

        # Create URL
        url = self.base_url + "operation"
        self.Debug_Message("setPosition", "URL: " + url)
        json = {"setcommands":[{"device_id": device_id ,"commands":[{"key":"position","value": str(position)}]}]}

        self.Debug_Message("setPosition", "for device " + str(json))

        try:
            myheaders = self.headers
            myheaders["ContentType"] = "application/json"
            myheaders["Authorization"] = self.access_token
            myheaders["Accept"] = "*/*"

            response = await session.post(url, headers=myheaders, json=json)

            if (response.status < 200) or (response.status >= 300):
                # server threw a error
                self.Debug_Message(
                    "setPosition",
                    "Error - response.status = " + str(response.status),
                )
                self.Debug_Message(
                    "setPosition", "Error - response.text= " + await response.text()
                )

            else:
                self.Debug_Message(
                    "setPosition",
                    "Success - response.ContentString = " + await response.text(),
                )

        except Exception as ex:
            LOGGER.error(
                f"{DOMAIN} Exception in setPosition : %s - traceback: %s",  # noqa: G004
                ex,
                traceback.format_exc(),
            )


    # ****************************************************************************************
    #
    # 		getCurrentPosition	-	Get current door position of device_id, returns int 0 to 100
    #
    # ****************************************************************************************

    async def getCurrentPosition(self, device_id: str):  # noqa: D102
        session = self._session
        await self.refreshAccessToken()

        # Create URL
        url = self.base_url + "operation/get"
        self.Debug_Message("getCurrentPosition", "URL: " + url)
        json = {"commands":[{"device_id": device_id ,"command": "position"}]}

        try:
            myheaders = self.headers
            myheaders["ContentType"] = "application/json"
            myheaders["Authorization"] = self.access_token
            myheaders["Accept"] = "*/*"

            response = await session.post(url, headers=myheaders, json=json)

            if (response.status < 200) or (response.status >= 300):
                # server threw a error
                self.Debug_Message(
                    "getCurrentPosition",
                    "Error - response.status = " + str(response.status),
                )
                self.Debug_Message(
                    "getCurrentPosition", "Error - response.text= " + await response.text()
                )

            else:
                self.Debug_Message(
                    "getCurrentPosition",
                    "Success - response.ContentString = " + await response.text(),
                )

                current_position = await response.json()

                return current_position["response"][0]["position"]

        except Exception as ex:
            LOGGER.error(
                f"{DOMAIN} Exception in getCurrentPosition : %s - traceback: %s",  # noqa: G004
                ex,
                traceback.format_exc(),
            )

    # async def async_get_data(self) -> any:
    #     """Get data from the API."""
    #     return await self._api_wrapper(
    #         method="get", url="https://jsonplaceholder.typicode.com/posts/1"
    #     )

    # async def async_set_title(self, value: str) -> any:
    #     """Get data from the API."""
    #     return await self._api_wrapper(
    #         method="patch",
    #         url="https://jsonplaceholder.typicode.com/posts/1",
    #         data={"title": value},
    #         headers={"Content-type": "application/json; charset=UTF-8"},
    #     )

    # async def _api_wrapper(
    #     self,
    #     method: str,
    #     url: str,
    #     data: dict | None = None,
    #     headers: dict | None = None,
    # ) -> any:
    #     """Get information from the API."""
    #     try:
    #         async with async_timeout.timeout(10):
    #             response = await self._session.request(
    #                 method=method,
    #                 url=url,
    #                 headers=headers,
    #                 json=data,
    #             )
    #             if response.status in (401, 403):
    #                 raise LycheeThingsApiClientAuthenticationError(
    #                     "Invalid credentials",
    #                 )
    #             response.raise_for_status()
    #             return await response.json()

    #     except asyncio.TimeoutError as exception:
    #         raise LycheeThingsApiClientCommunicationError(
    #             "Timeout error fetching information",
    #         ) from exception
    #     except (aiohttp.ClientError, socket.gaierror) as exception:
    #         raise LycheeThingsApiClientCommunicationError(
    #             "Error fetching information",
    #         ) from exception
    #     except Exception as exception:  # pylint: disable=broad-except
    #         raise LycheeThingsApiClientError(
    #             "Something really wrong happened!"
    #         ) from exception
